"""
AVENZO Backend — Inventory & Transaction Audit Test Suite
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_inventory_stock_adjustment_and_audit(client: AsyncClient, admin_headers: dict, staff_headers: dict):
    """Test inventory stock additions, reductions, stock balance check, and transaction audit log creation."""
    # Setup Product, Category, Warehouse, Location, Batch
    cat_res = await client.post("/api/v1/categories", json={"name": "Inventory Test Category"}, headers=admin_headers)
    cat_id = cat_res.json()["data"]["id"]

    prod_res = await client.post(
        "/api/v1/products",
        json={"name": "Organic Honey 500g", "sku": "HONEY-500G-INV", "category_id": cat_id, "unit_price": "250.00"},
        headers=admin_headers,
    )
    prod_id = prod_res.json()["data"]["id"]

    wh_res = await client.post(
        "/api/v1/warehouses", json={"name": "Main Inventory Warehouse", "city": "Pune"}, headers=admin_headers
    )
    wh_id = wh_res.json()["data"]["id"]

    batch_res = await client.post(
        "/api/v1/batches",
        json={"product_id": prod_id, "batch_number": "BATCH-HONEY-001", "initial_quantity": 100},
        headers=staff_headers,
    )
    batch_id = batch_res.json()["data"]["id"]

    # Stock Addition (Receipt)
    adjust_add_payload = {
        "product_id": prod_id,
        "batch_id": batch_id,
        "warehouse_id": wh_id,
        "quantity_change": 100,
        "transaction_type": "RECEIPT",
        "notes": "Initial stock receiving",
    }

    add_res = await client.post("/api/v1/inventory/adjust", json=adjust_add_payload, headers=staff_headers)
    assert add_res.status_code == 200
    inv_data = add_res.json()["data"]
    assert inv_data["quantity_on_hand"] == 100
    assert inv_data["quantity_available"] == 100
    inv_id = inv_data["id"]

    # Stock Reduction (Adjustment/Damage)
    adjust_sub_payload = {
        "product_id": prod_id,
        "batch_id": batch_id,
        "warehouse_id": wh_id,
        "quantity_change": -20,
        "transaction_type": "DAMAGE",
        "notes": "Damaged during handling",
    }
    sub_res = await client.post("/api/v1/inventory/adjust", json=adjust_sub_payload, headers=staff_headers)
    assert sub_res.status_code == 200
    sub_data = sub_res.json()["data"]
    assert sub_data["quantity_on_hand"] == 80

    # Stock Reduction exceeding available stock must fail with 400
    excess_sub_payload = {
        "product_id": prod_id,
        "batch_id": batch_id,
        "warehouse_id": wh_id,
        "quantity_change": -500,
        "transaction_type": "ADJUSTMENT",
    }
    excess_res = await client.post("/api/v1/inventory/adjust", json=excess_sub_payload, headers=staff_headers)
    assert excess_res.status_code == 400

    # Verify Audit Transactions Log
    tx_res = await client.get(f"/api/v1/inventory/transactions?inventory_id={inv_id}", headers=staff_headers)
    assert tx_res.status_code == 200
    tx_list = tx_res.json()["data"]
    assert len(tx_list) >= 2
    types = [t["transaction_type"] for t in tx_list]
    assert "RECEIPT" in types
    assert "DAMAGE" in types
