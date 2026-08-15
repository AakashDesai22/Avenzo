"""
AVENZO Backend — Category API & RBAC Test Suite
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_category_list_public(client: AsyncClient):
    """Test listing categories is accessible publicly/authenticated."""
    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_category_create_admin(client: AsyncClient, admin_headers: dict):
    """Test category creation by Admin user."""
    payload = {
        "name": "Dairy & Milk Products",
        "description": "Perishable dairy catalogue",
        "is_active": True,
    }
    response = await client.post("/api/v1/categories", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Dairy & Milk Products"
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_category_create_forbidden_for_consumer(client: AsyncClient, consumer_headers: dict):
    """Test category creation fails with 403 Forbidden for Consumer role."""
    payload = {"name": "Unauthorized Category"}
    response = await client.post("/api/v1/categories", json=payload, headers=consumer_headers)
    assert response.status_code == 403
    assert "does not have permission" in response.json()["detail"]


@pytest.mark.asyncio
async def test_category_update_and_get(client: AsyncClient, admin_headers: dict):
    """Test updating and fetching a category."""
    create_res = await client.post("/api/v1/categories", json={"name": "Beverages"}, headers=admin_headers)
    cat_id = create_res.json()["data"]["id"]

    # Get by ID
    get_res = await client.get(f"/api/v1/categories/{cat_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == "Beverages"

    # Update
    update_res = await client.put(f"/api/v1/categories/{cat_id}", json={"description": "Cold & Hot drinks"}, headers=admin_headers)
    assert update_res.status_code == 200
    assert update_res.json()["data"]["description"] == "Cold & Hot drinks"
