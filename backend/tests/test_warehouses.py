"""
AVENZO Backend — Warehouse & Location Test Suite
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_warehouse_and_location_flow(client: AsyncClient, admin_headers: dict, staff_headers: dict):
    """Test warehouse creation, location addition, and retrieval by Staff."""
    # Create Warehouse
    wh_payload = {
        "name": "Central Distribution Center",
        "address": "Plot 42, Logistics Park",
        "city": "Mumbai",
        "is_active": True,
    }
    create_res = await client.post("/api/v1/warehouses", json=wh_payload, headers=admin_headers)
    assert create_res.status_code == 201
    wh_id = create_res.json()["data"]["id"]

    # Add Location to Warehouse
    loc_payload = {
        "location_code": "AISLE-A1-BIN04",
        "description": "Cold Storage Section A",
    }
    loc_res = await client.post(f"/api/v1/warehouses/{wh_id}/locations", json=loc_payload, headers=admin_headers)
    assert loc_res.status_code == 201
    assert loc_res.json()["data"]["location_code"] == "AISLE-A1-BIN04"

    # Staff can view warehouse and its locations
    get_res = await client.get(f"/api/v1/warehouses/{wh_id}", headers=staff_headers)
    assert get_res.status_code == 200
    wh_data = get_res.json()["data"]
    assert wh_data["name"] == "Central Distribution Center"
    assert len(wh_data["locations"]) >= 1

    # Update Warehouse (Admin only)
    update_res = await client.put(
        f"/api/v1/warehouses/{wh_id}",
        json={"name": "Central Distribution Center - Updated", "city": "Navi Mumbai"},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["name"] == "Central Distribution Center - Updated"
    assert update_res.json()["data"]["city"] == "Navi Mumbai"

    # Deactivate Warehouse when no active stock exists
    del_res = await client.delete(f"/api/v1/warehouses/{wh_id}", headers=admin_headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["is_active"] is False


@pytest.mark.asyncio
async def test_warehouse_deactivation_blocked_by_active_inventory(
    client: AsyncClient, admin_headers: dict, staff_headers: dict
):
    """Warehouse cannot be deactivated if it has active stock balances."""
    # 1. Create category, product, warehouse, batch
    cat_res = await client.post("/api/v1/categories", json={"name": "Wh Test Cat"}, headers=admin_headers)
    cat_id = cat_res.json()["data"]["id"]

    prod_res = await client.post(
        "/api/v1/products",
        json={"name": "Wh Test Product", "sku": f"WH-PROD-SKU", "category_id": cat_id, "unit_price": "100.00"},
        headers=admin_headers,
    )
    prod_id = prod_res.json()["data"]["id"]

    wh_res = await client.post(
        "/api/v1/warehouses", json={"name": "Protected Warehouse", "city": "Pune"}, headers=admin_headers
    )
    wh_id = wh_res.json()["data"]["id"]

    batch_res = await client.post(
        "/api/v1/batches",
        json={"product_id": prod_id, "batch_number": "WH-BATCH-001", "initial_quantity": 50},
        headers=staff_headers,
    )
    batch_id = batch_res.json()["data"]["id"]

    # 2. Add active stock to the warehouse
    adj_res = await client.post(
        "/api/v1/inventory/adjust",
        json={
            "product_id": prod_id,
            "batch_id": batch_id,
            "warehouse_id": wh_id,
            "quantity_change": 50,
            "transaction_type": "RECEIPT",
            "notes": "Stock receipt for protection test",
        },
        headers=staff_headers,
    )
    assert adj_res.status_code == 200

    # 3. Attempt to deactivate warehouse -> should fail with 400
    del_res = await client.delete(f"/api/v1/warehouses/{wh_id}", headers=admin_headers)
    assert del_res.status_code == 400
    assert "active inventory" in del_res.json()["detail"].lower()

