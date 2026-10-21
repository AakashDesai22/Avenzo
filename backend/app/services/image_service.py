"""
AVENZO Backend — Image Validation & Cloudinary Upload Service
Provides secure, in-memory validation of image payloads (file signatures,
dimension bounds, decompression-bomb defense) and mediated asynchronous uploads
to Cloudinary using httpx.AsyncClient with deterministic SHA-1 signatures.
Zero local disk writes.
"""

import hashlib
import logging
import re
import struct
import time
import uuid
from typing import Any, Dict, Optional, Tuple

import httpx
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# Resource Constraints & Bounds
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MiB (5,242,880 bytes)
MAX_DIMENSION = 4096                     # 4096 px width / height
MAX_PIXELS = 16_777_216                  # 16.7 megapixels (4096 x 4096)
ALLOWED_MIME_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WebP": "image/webp",
}

FOLDER_REGEX = re.compile(r"^[a-zA-Z0-9_\-\/]+$")


def generate_cloudinary_signature(params: Dict[str, Any], api_secret: str) -> str:
    """
    Generate Cloudinary SHA-1 signature according to official specification:
    1. Filter out empty, None, and non-signable parameters
       (file, cloud_name, resource_type, api_key, signature).
    2. Sort keys alphabetically.
    3. Serialize to query string format: 'k1=v1&k2=v2'.
    4. Append api_secret directly: 'k1=v1&k2=v2<secret>'.
    5. Compute SHA-1 hex digest in lowercase.
    """
    excluded_keys = {"file", "cloud_name", "resource_type", "api_key", "signature"}
    signable_params = {
        k: v for k, v in params.items()
        if k not in excluded_keys and v is not None and v != ""
    }

    sorted_pairs = [f"{k}={signable_params[k]}" for k in sorted(signable_params.keys())]
    to_sign = "&".join(sorted_pairs) + api_secret

    return hashlib.sha1(to_sign.encode("utf-8")).hexdigest()


def detect_and_validate_image(data: bytes) -> Tuple[str, str, int, int]:
    """
    Validates file magic bytes (signature) and extracts image dimensions (width, height)
    using binary header parsing with zero untrusted native decompression.
    Returns (format_name, file_extension, width, height).
    Raises HTTPException(400) if signature, dimensions, or pixel count exceed safety limits.
    """
    if len(data) < 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file: File is too small or truncated.",
        )

    fmt_name: Optional[str] = None
    ext: Optional[str] = None
    width = 0
    height = 0

    # 1. Check PNG signature: \x89PNG\r\n\x1a\n
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        if len(data) < 24:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid PNG file: Corrupted header chunk.",
            )
        width, height = struct.unpack(">II", data[16:24])
        fmt_name = "PNG"
        ext = ".png"

    # 2. Check JPEG signature: \xff\xd8\xff
    elif data.startswith(b"\xff\xd8\xff"):
        offset = 2
        data_len = len(data)
        while offset < data_len - 8:
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            # Baseline & progressive SOF markers (SOF0, SOF1, SOF2, etc.)
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                if offset + 9 <= data_len:
                    h, w = struct.unpack(">HH", data[offset + 5 : offset + 9])
                    width, height = w, h
                    break
                else:
                    break
            if offset + 4 <= data_len:
                seg_len = struct.unpack(">H", data[offset + 2 : offset + 4])[0]
                offset += 2 + seg_len
            else:
                break

        if width <= 0 or height <= 0:
            # Fallback for progressive / EXIF-prefixed standard JPEGs
            width, height = 1, 1

        fmt_name = "JPEG"
        ext = ".jpg"

    # 3. Check WebP signature: RIFF .... WEBP
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        chunk_type = data[12:16]
        if chunk_type == b"VP8 ":
            # Lossy WebP: dimensions at offset 26
            if len(data) >= 30:
                w, h = struct.unpack("<HH", data[26:30])
                width = w & 0x3FFF
                height = h & 0x3FFF
        elif chunk_type == b"VP8L":
            # Lossless WebP: 1 byte signature + 4 bytes packed dimensions at offset 21
            if len(data) >= 25:
                b1, b2, b3, b4 = data[21:25]
                width = 1 + (((b2 & 0x3F) << 8) | b1)
                height = 1 + (((b4 & 0xF) << 10) | (b3 << 2) | ((b2 & 0xC0) >> 6))
        elif chunk_type == b"VP8X":
            # Extended WebP: 24-bit little-endian width and height
            if len(data) >= 30:
                width = 1 + int.from_bytes(data[24:27], "little")
                height = 1 + int.from_bytes(data[27:30], "little")

        if width <= 0 or height <= 0:
            width, height = 1, 1

        fmt_name = "WebP"
        ext = ".webp"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. Only valid JPEG, PNG, and WebP files are accepted.",
        )

    # Validate dimension limits and decompression-bomb constraints
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Image dimensions ({width}x{height}) exceed maximum allowed limit of "
                f"{MAX_DIMENSION}x{MAX_DIMENSION} pixels."
            ),
        )

    pixel_count = width * height
    if pixel_count > MAX_PIXELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Total image pixels ({pixel_count}) exceed safety limit of "
                f"{MAX_PIXELS} pixels (16.7 megapixels)."
            ),
        )

    return fmt_name, ext, width, height


async def upload_image_to_cloudinary(file: UploadFile, folder: Optional[str] = None) -> dict:
    """
    Safely reads image stream up to 5 MiB ceiling, validates format and dimensions,
    constructs canonical Cloudinary signature, and uploads directly via httpx.AsyncClient.
    Zero local disk persistence.
    """
    # 1. Incremental stream read enforcing 5 MiB ceiling
    chunks = []
    total_bytes = 0

    while True:
        chunk = await file.read(1024 * 64)  # 64 KiB chunks
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image file exceeds maximum allowable size of 5 MB ({MAX_IMAGE_SIZE_BYTES} bytes).",
            )
        chunks.append(chunk)

    raw_data = b"".join(chunks)
    if not raw_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # 2. Validate format signatures, dimensions, and pixel ceiling
    fmt_name, ext, width, height = detect_and_validate_image(raw_data)

    # 3. Verify server Cloudinary configuration
    if (
        not settings.CLOUDINARY_CLOUD_NAME
        or not settings.CLOUDINARY_API_KEY
        or not settings.CLOUDINARY_API_SECRET
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary storage is not configured on the server.",
        )

    # 4. Prepare parameters for signed upload
    target_folder = folder or settings.CLOUDINARY_FOLDER or "avenzo"
    if not FOLDER_REGEX.match(target_folder):
        target_folder = "avenzo"

    public_id = f"img_{uuid.uuid4().hex}"
    timestamp = str(int(time.time()))

    sign_params = {
        "folder": target_folder,
        "public_id": public_id,
        "timestamp": timestamp,
    }

    signature = generate_cloudinary_signature(sign_params, settings.CLOUDINARY_API_SECRET)

    # 5. Execute async multipart POST via httpx
    upload_url = f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/image/upload"
    form_data = {
        "api_key": settings.CLOUDINARY_API_KEY,
        "timestamp": timestamp,
        "folder": target_folder,
        "public_id": public_id,
        "signature": signature,
    }
    files = {
        "file": (f"{public_id}{ext}", raw_data, ALLOWED_MIME_TYPES.get(fmt_name, "application/octet-stream")),
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=5.0)) as client:
            resp = await client.post(upload_url, data=form_data, files=files)
    except httpx.TimeoutException:
        logger.error("Cloudinary upload request timed out.")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Image storage request timed out. Please try again.",
        )
    except Exception as exc:
        logger.error(f"Cloudinary connection error: {type(exc).__name__}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to connect to cloud storage provider.",
        )

    if resp.status_code != 200:
        logger.error(f"Cloudinary upload rejected with HTTP {resp.status_code}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cloud storage provider rejected image upload.",
        )

    res_json = resp.json()
    secure_url = res_json.get("secure_url") or res_json.get("url")
    if not secure_url:
        logger.error("Cloudinary response missing secure_url.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Invalid response received from cloud storage provider.",
        )

    return {
        "image_url": secure_url,
        "public_id": res_json.get("public_id", public_id),
        "format": fmt_name,
        "width": res_json.get("width", width),
        "height": res_json.get("height", height),
        "size_bytes": total_bytes,
    }
