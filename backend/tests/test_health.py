"""
AVENZO Backend — Test Suite: Health Endpoint
Tests for GET /health and GET /api/v1/health endpoints.

Run with:
    cd backend
    pytest tests/test_health.py -v
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_root_health_check():
    """
    Test GET /health returns 200 with healthy status.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "avenzo-backend"
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_api_v1_health_check():
    """
    Test GET /api/v1/health returns 200 with detailed health status.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "avenzo-backend"
    assert data["status"] == "healthy"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "components" in data
    assert data["components"]["api"] == "healthy"


@pytest.mark.asyncio
async def test_health_response_contains_timestamp():
    """
    Test that the health response timestamp is an ISO 8601 string.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    # Basic ISO 8601 format check
    timestamp = data.get("timestamp", "")
    assert "T" in timestamp
    assert "Z" in timestamp or "+" in timestamp


@pytest.mark.asyncio
async def test_unknown_endpoint_returns_404():
    """
    Test that unknown endpoints return 404.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/unknown-endpoint")

    assert response.status_code == 404
