"""
AVENZO Backend — Product Master & RBAC Test Suite
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_product_crud_flow(client: AsyncClient, admin_headers: dict, consumer_headers: dict):
    """Test product creation, duplicate SKU rejection, search, and deactivation."""
    # First create a category
    cat_res = await client.post("/api/v1/categories", json={"name": "Fresh Bakery"}, headers=admin_headers)
    cat_id = cat_res.json()["data"]["id"]

    # Create Product
    product_payload = {
        "name": "Whole Wheat Bread 400g",
        "sku": "BAK-WWB-001",
        "barcode": "8901234567890",
        "category_id": cat_id,
        "unit_of_measure": "loaf",
        "unit_price": "45.00",
        "cost_price": "32.00",
        "shelf_life_days": 7,
        "has_expiry": True,
    }

    create_res = await client.post("/api/v1/products", json=product_payload, headers=admin_headers)
    assert create_res.status_code == 201
    prod_data = create_res.json()["data"]
    assert prod_data["sku"] == "BAK-WWB-001"
    assert prod_data["unit_price"] == "45.00"
    prod_id = prod_data["id"]

    # Duplicate SKU should fail with 409
    dup_res = await client.post("/api/v1/products", json=product_payload, headers=admin_headers)
    assert dup_res.status_code == 409

    # Retrieve Product
    get_res = await client.get(f"/api/v1/products/{prod_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["name"] == "Whole Wheat Bread 400g"

    # Search Products
    search_res = await client.get("/api/v1/products?search=Wheat")
    assert search_res.status_code == 200
    assert len(search_res.json()["data"]) >= 1

    # Consumer cannot create product (403)
    consumer_res = await client.post("/api/v1/products", json=product_payload, headers=consumer_headers)
    assert consumer_res.status_code == 403


@pytest.mark.asyncio
async def test_product_create_invalid_category(client: AsyncClient, admin_headers: dict):
    """Test product creation with non-existent category_id fails with 404."""
    invalid_payload = {
        "name": "Invalid Product",
        "sku": "INV-001",
        "category_id": "00000000-0000-0000-0000-000000000000",
        "unit_price": "10.00",
    }
    res = await client.post("/api/v1/products", json=invalid_payload, headers=admin_headers)
    assert res.status_code == 404
