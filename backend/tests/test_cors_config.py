"""
AVENZO Backend — Tests for CORS Configuration and Preflight Handling
Tests canonical vs legacy variable support, deterministic precedence,
origin trimming and normalization, production wildcard rejection, and ASGI preflight responses.
"""

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


def test_default_allowed_origins():
    """Verify default CORS origins when no environment variable is provided."""
    with patch.dict("os.environ", {}, clear=True):
        s = Settings(_env_file=None)
        assert s.ALLOWED_ORIGINS == ["http://localhost:5173", "http://localhost:3000"]


def test_canonical_allowed_origins_env():
    """Verify canonical ALLOWED_ORIGINS loads production frontend domain."""
    env = {"ALLOWED_ORIGINS": "https://avenzo.teammavericks.org,http://localhost:5173"}
    with patch.dict("os.environ", env, clear=True):
        s = Settings(_env_file=None)
        assert s.ALLOWED_ORIGINS == [
            "https://avenzo.teammavericks.org",
            "http://localhost:5173",
        ]
        assert "https://avenzo.teammavericks.org" in s.ALLOWED_ORIGINS


def test_legacy_allowed_origins_str_env():
    """Verify backward compatibility with legacy ALLOWED_ORIGINS_STR."""
    env = {"ALLOWED_ORIGINS_STR": "https://avenzo.teammavericks.org,http://localhost:3000"}
    with patch.dict("os.environ", env, clear=True):
        s = Settings(_env_file=None)
        assert s.ALLOWED_ORIGINS == [
            "https://avenzo.teammavericks.org",
            "http://localhost:3000",
        ]
        assert "https://avenzo.teammavericks.org" in s.ALLOWED_ORIGINS


def test_deterministic_precedence_canonical_over_legacy():
    """Verify deterministic precedence: ALLOWED_ORIGINS takes priority over ALLOWED_ORIGINS_STR."""
    env = {
        "ALLOWED_ORIGINS": "https://canonical-origin.com",
        "ALLOWED_ORIGINS_STR": "https://legacy-origin.com",
    }
    with patch.dict("os.environ", env, clear=True):
        s = Settings(_env_file=None)
        assert s.ALLOWED_ORIGINS == ["https://canonical-origin.com"]
        assert "https://legacy-origin.com" not in s.ALLOWED_ORIGINS


def test_origin_parsing_trim_empty_and_trailing_slashes():
    """Verify origins are trimmed, empty entries ignored, duplicates merged, and trailing slashes stripped."""
    env = {
        "ALLOWED_ORIGINS": (
            " https://avenzo.teammavericks.org/ , , http://localhost:5173/ , "
            "https://avenzo.teammavericks.org "
        )
    }
    with patch.dict("os.environ", env, clear=True):
        s = Settings(_env_file=None)
        assert s.ALLOWED_ORIGINS == [
            "https://avenzo.teammavericks.org",
            "http://localhost:5173",
        ]


def test_wildcard_rejected_in_production():
    """Verify that wildcard '*' is rejected in production mode to prevent insecure credentialed requests."""
    env = {
        "APP_ENV": "production",
        "APP_DEBUG": "false",
        "JWT_SECRET": "a" * 32,
        "EXPIRY_MONITOR_SECRET": "b" * 16,
        "ALLOWED_ORIGINS": "https://avenzo.teammavericks.org,*",
    }
    with (
        patch.dict("os.environ", env, clear=True),
        pytest.raises(ValueError, match="Wildcard '\\*' origin is not permitted"),
    ):
        Settings(_env_file=None)


@pytest.mark.asyncio
async def test_cors_preflight_options_allowed_origin():
    """Verify that HTTP OPTIONS preflight request from allowed origin receives CORS response headers."""
    env = {"ALLOWED_ORIGINS": "https://avenzo.teammavericks.org,http://localhost:5173"}
    with patch.dict("os.environ", env, clear=True):
        test_settings = Settings(_env_file=None)
        with patch("app.main.settings", test_settings):
            app = create_app()
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                headers = {
                    "Origin": "https://avenzo.teammavericks.org",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type,authorization",
                }
                response = await client.options("/api/v1/auth/login", headers=headers)
                assert response.status_code == 200
                assert (
                    response.headers.get("access-control-allow-origin")
                    == "https://avenzo.teammavericks.org"
                )
                assert response.headers.get("access-control-allow-credentials") == "true"
                assert "POST" in response.headers.get("access-control-allow-methods", "")


@pytest.mark.asyncio
async def test_cors_preflight_options_disallowed_origin():
    """Verify that HTTP OPTIONS preflight request from an unallowed origin is rejected without CORS headers."""
    env = {"ALLOWED_ORIGINS": "https://avenzo.teammavericks.org"}
    with patch.dict("os.environ", env, clear=True):
        test_settings = Settings(_env_file=None)
        with patch("app.main.settings", test_settings):
            app = create_app()
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                headers = {
                    "Origin": "https://unauthorized-attacker.com",
                    "Access-Control-Request-Method": "POST",
                }
                response = await client.options("/api/v1/auth/login", headers=headers)
                # Disallowed origin does not get Access-Control-Allow-Origin header
                assert "access-control-allow-origin" not in response.headers
