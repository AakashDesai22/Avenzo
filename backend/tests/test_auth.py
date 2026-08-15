"""
AVENZO Backend — Authentication & RBAC Test Suite
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration(client: AsyncClient):
    """Test self-registration endpoint."""
    payload = {
        "email": "consumer_test@avenzo.dev",
        "password": "SecurePassword123!",
        "first_name": "Jane",
        "last_name": "Consumer",
        "phone": "+1234567890",
        "user_type": "consumer",
    }

    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "consumer_test@avenzo.dev"
    assert data["data"]["user_type"] == "consumer"
    assert "password_hash" not in data["data"]


@pytest.mark.asyncio
async def test_user_login_success(client: AsyncClient):
    """Test valid login returns tokens and user profile."""
    # Register first
    reg_payload = {
        "email": "login_test@avenzo.dev",
        "password": "MySecretPassword123!",
        "first_name": "John",
        "last_name": "Staff",
        "user_type": "business",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "login_test@avenzo.dev",
        "password": "MySecretPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["user"]["email"] == "login_test@avenzo.dev"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with wrong password fails with 401."""
    login_payload = {
        "email": "nonexistent@avenzo.dev",
        "password": "WrongPassword!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient):
    """Test GET /api/v1/auth/me returns profile for authenticated user."""
    reg_payload = {
        "email": "profile_test@avenzo.dev",
        "password": "MySecretPassword123!",
        "first_name": "Alice",
        "last_name": "Smith",
        "user_type": "consumer",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_resp = await client.post("/api/v1/auth/login", json={"email": "profile_test@avenzo.dev", "password": "MySecretPassword123!"})
    token = login_resp.json()["data"]["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["data"]["email"] == "profile_test@avenzo.dev"
    assert me_data["data"]["first_name"] == "Alice"
