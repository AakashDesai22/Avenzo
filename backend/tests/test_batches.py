"""
AVENZO Backend — Batch API & Date Validation Test Suite
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_batch_creation_and_date_validation(client: AsyncClient, admin_headers: dict, staff_headers: dict):
    """Test batch creation, date constraint validation (expiry >= manufacturing), and retrieval."""
    # Setup Category + Product
    cat_res = await client.post("/api/v1/categories", json={"name": "Dairy Batch Test"}, headers=admin_headers)
    cat_id = cat_res.json()["data"]["id"]

    prod_res = await client.post(
        "/api/v1/products",
        json={"name": "Pasteurized Milk 1L", "sku": "MILK-1L-BATCH", "category_id": cat_id, "unit_price": "60.00"},
        headers=admin_headers,
    )
    prod_id = prod_res.json()["data"]["id"]

    # Valid Batch creation by Staff
    valid_batch = {
        "product_id": prod_id,
        "batch_number": "BATCH-2026-08A",
        "manufacturing_date": "2026-08-10",
        "expiry_date": "2026-08-25",
        "initial_quantity": 500,
        "status": "active",
    }
    create_res = await client.post("/api/v1/batches", json=valid_batch, headers=staff_headers)
    assert create_res.status_code == 201
    batch_data = create_res.json()["data"]
    assert batch_data["batch_number"] == "BATCH-2026-08A"
    assert batch_data["initial_quantity"] == 500
    batch_id = batch_data["id"]

    # Invalid Batch (Expiry before Manufacturing date) must fail with 422 (Pydantic validator) or 400
    invalid_batch = {
        "product_id": prod_id,
        "batch_number": "BATCH-INVALID-DATES",
        "manufacturing_date": "2026-08-25",
        "expiry_date": "2026-08-10", # Invalid! Expiry before Mfg
    }
    inv_res = await client.post("/api/v1/batches", json=invalid_batch, headers=staff_headers)
    assert inv_res.status_code in [400, 422]

    # Get Batch by ID
    get_res = await client.get(f"/api/v1/batches/{batch_id}", headers=staff_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["batch_number"] == "BATCH-2026-08A"
