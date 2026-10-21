"""
AVENZO Backend — Media & Image Uploads Test Suite
Verifies image validation (magic bytes, dimensions <= 4096px, size <= 5MB,
decompression-bomb mitigation), canonical Cloudinary signature generation,
RBAC (ADMIN/BUSINESS_MANAGER vs CONSUMER), and async httpx Cloudinary upload mocks.
Zero real credentials; zero external network requests.
"""

import io
import struct
from unittest.mock import AsyncMock, patch

import pytest
import httpx
from httpx import AsyncClient

from app.core.config import settings
from app.services.image_service import (
    MAX_DIMENSION,
    MAX_IMAGE_SIZE_BYTES,
    detect_and_validate_image,
    generate_cloudinary_signature,
)

# 1x1 Transparent PNG binary (valid header, 1x1 dimensions)
SAMPLE_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    b"\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)

# Minimal 1x1 JPEG binary (valid SOF0 header, 1x1 dimensions)
SAMPLE_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07"
    b"\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
    b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)

# Minimal Lossless WebP binary (1x1 pixel)
SAMPLE_WEBP = (
    b"RIFF\x1a\x00\x00\x00WEBPVP8L\x0d\x00\x00\x00/\x00\x00\x00\x00\x07\x01\x02\x00\x00\xfe\x01\x00"
)

MOCK_CLOUDINARY_RESPONSE = {
    "public_id": "avenzo/sample_12345",
    "version": 1729500000,
    "width": 1,
    "height": 1,
    "format": "png",
    "bytes": 68,
    "secure_url": "https://res.cloudinary.com/demo_cloud/image/upload/v1729500000/avenzo/sample_12345.png",
    "url": "http://res.cloudinary.com/demo_cloud/image/upload/v1729500000/avenzo/sample_12345.png",
}


def test_cloudinary_signature_generation_canonical_ordering():
    """
    Tests Cloudinary SHA-1 signing according to official specification:
    - Sorts parameters alphabetically.
    - Excludes file, api_key, cloud_name, resource_type, signature, and None/empty.
    - Appends secret directly and hashes via SHA-1.
    """
    params = {
        "timestamp": 1315060510,
        "public_id": "sample_image",
        "folder": "products",
        "api_key": "1234567890",      # must be excluded
        "file": b"binary_data",        # must be excluded
        "empty_val": "",               # must be excluded
        "none_val": None,              # must be excluded
    }
    secret = "abcd1234secret"
    # Canonical string to sign: "folder=products&public_id=sample_image&timestamp=1315060510abcd1234secret"
    import hashlib
    expected_to_sign = "folder=products&public_id=sample_image&timestamp=1315060510abcd1234secret"
    expected_hash = hashlib.sha1(expected_to_sign.encode("utf-8")).hexdigest()

    sig = generate_cloudinary_signature(params, secret)
    assert sig == expected_hash


def test_detect_image_valid_formats():
    """Detects valid PNG, JPEG, and WebP binaries and extracts dimensions."""
    fmt, ext, w, h = detect_and_validate_image(SAMPLE_PNG)
    assert fmt == "PNG" and ext == ".png" and w == 1 and h == 1

    fmt, ext, w, h = detect_and_validate_image(SAMPLE_JPEG)
    assert fmt == "JPEG" and ext == ".jpg" and w == 1 and h == 1

    fmt, ext, w, h = detect_and_validate_image(SAMPLE_WEBP)
    assert fmt == "WebP" and ext == ".webp" and w == 1 and h == 1


def test_detect_image_rejects_decompression_bomb():
    """Rejects images exceeding MAX_DIMENSION (4096px) or MAX_PIXELS (16.7 MP)."""
    # Create fake PNG header claiming 5000x5000 dimensions
    fake_png_header = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        + struct.pack(">II", 5000, 5000)
        + b"\x08\x06\x00\x00\x00"
    )
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        detect_and_validate_image(fake_png_header)
    assert exc_info.value.status_code == 400
    assert "exceed maximum allowed limit" in exc_info.value.detail


@pytest.mark.asyncio
async def test_upload_image_unauthenticated_rejected(client: AsyncClient):
    """Unauthenticated requests must be rejected with 401 or 403."""
    files = {"file": ("test.png", io.BytesIO(SAMPLE_PNG), "image/png")}
    res = await client.post("/api/v1/uploads/image", files=files)
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_upload_image_consumer_rejected(client: AsyncClient, consumer_headers: dict):
    """Consumer role cannot upload catalog media."""
    files = {"file": ("test.png", io.BytesIO(SAMPLE_PNG), "image/png")}
    res = await client.post("/api/v1/uploads/image", files=files, headers=consumer_headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_upload_png_success_mocked(client: AsyncClient, admin_headers: dict, monkeypatch):
    """Admin uploading valid PNG succeeds when Cloudinary credentials are set and returns secure_url."""
    monkeypatch.setattr(settings, "CLOUDINARY_CLOUD_NAME", "test-cloud")
    monkeypatch.setattr(settings, "CLOUDINARY_API_KEY", "111222333")
    monkeypatch.setattr(settings, "CLOUDINARY_API_SECRET", "test_secret_32chars_long_123456789")

    mock_resp = httpx.Response(
        status_code=200,
        json=MOCK_CLOUDINARY_RESPONSE,
        request=httpx.Request("POST", "https://api.cloudinary.com/v1_1/test-cloud/image/upload"),
    )

    mock_async_client = AsyncMock()
    mock_async_client.post.return_value = mock_resp
    mock_async_client.__aenter__.return_value = mock_async_client
    mock_async_client.__aexit__.return_value = None

    with patch("app.services.image_service.httpx.AsyncClient", return_value=mock_async_client):
        files = {"file": ("sample.png", io.BytesIO(SAMPLE_PNG), "image/png")}
        res = await client.post("/api/v1/uploads/image", files=files, headers=admin_headers)

        assert res.status_code == 201
        data = res.json()["data"]
        assert data["image_url"].startswith("https://res.cloudinary.com/")
        assert data["public_id"] == "avenzo/sample_12345"
        assert data["format"] == "PNG"
        assert data["width"] == 1
        assert data["height"] == 1


@pytest.mark.asyncio
async def test_upload_unconfigured_cloudinary_returns_503(client: AsyncClient, admin_headers: dict, monkeypatch):
    """When Cloudinary settings are missing, returns 503 Service Unavailable."""
    monkeypatch.setattr(settings, "CLOUDINARY_CLOUD_NAME", "")
    monkeypatch.setattr(settings, "CLOUDINARY_API_KEY", "")
    monkeypatch.setattr(settings, "CLOUDINARY_API_SECRET", "")

    files = {"file": ("sample.png", io.BytesIO(SAMPLE_PNG), "image/png")}
    res = await client.post("/api/v1/uploads/image", files=files, headers=admin_headers)
    assert res.status_code == 503
    assert "not configured" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_unsupported_file_rejected(client: AsyncClient, admin_headers: dict):
    """Files with non-image content are rejected with 400 Bad Request."""
    fake_data = b"Hello, this is plain text masquerading as an image."
    files = {"file": ("fake.png", io.BytesIO(fake_data), "image/png")}
    res = await client.post("/api/v1/uploads/image", files=files, headers=admin_headers)
    assert res.status_code == 400
    assert "unsupported" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_exceeds_max_size_rejected_413(client: AsyncClient, admin_headers: dict):
    """Files exceeding 5 MB ceiling are rejected with 413 Payload Too Large."""
    # 5 MB + 100 KB
    oversized_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * (MAX_IMAGE_SIZE_BYTES + 100)
    files = {"file": ("oversized.png", io.BytesIO(oversized_data), "image/png")}
    res = await client.post("/api/v1/uploads/image", files=files, headers=admin_headers)
    assert res.status_code == 413
    assert "5 mb" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_cloudinary_timeout_returns_504(client: AsyncClient, admin_headers: dict, monkeypatch):
    """When upstream Cloudinary times out, returns 504 Gateway Timeout without leaking secrets."""
    monkeypatch.setattr(settings, "CLOUDINARY_CLOUD_NAME", "test-cloud")
    monkeypatch.setattr(settings, "CLOUDINARY_API_KEY", "111222333")
    monkeypatch.setattr(settings, "CLOUDINARY_API_SECRET", "super_secret_key_1234567890")

    mock_async_client = AsyncMock()
    mock_async_client.post.side_effect = httpx.TimeoutException("Connection timed out")
    mock_async_client.__aenter__.return_value = mock_async_client
    mock_async_client.__aexit__.return_value = None

    with patch("app.services.image_service.httpx.AsyncClient", return_value=mock_async_client):
        files = {"file": ("sample.png", io.BytesIO(SAMPLE_PNG), "image/png")}
        res = await client.post("/api/v1/uploads/image", files=files, headers=admin_headers)

        assert res.status_code == 504
        assert "timed out" in res.json()["detail"].lower()
        # Verify secret not leaked in error payload
        assert "super_secret_key_1234567890" not in res.text
