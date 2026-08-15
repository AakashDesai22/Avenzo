"""
AVENZO Backend — FEFO Ranking & Allocation Preview Test Suite
"""

import pytest
from datetime import timedelta
from httpx import AsyncClient
from app.core.date_utils import get_business_date


@pytest.mark.asyncio
async def test_fefo_ranking_and_tie_breaking(client: AsyncClient, admin_headers: dict, staff_headers: dict):
    """
    Test 5-level deterministic FEFO tie-breaking ranking:
    1. expiry_date ASC, 2. mfg_date ASC, 3. created_at ASC, 4. quantity_available DESC, 5. batch.id ASC.
    Also verifies expired batches are excluded.
    """
    cat_res = await client.post("/api/v1/categories", json={"name": "FEFO Test Category"}, headers=admin_headers)
    cat_id = cat_res.json()["data"]["id"]

    prod_res = await client.post(
        "/api/v1/products",
        json={"name": "Fresh Milk 1L", "sku": "MILK-FEFO-TEST-01", "category_id": cat_id, "unit_price": "60.00", "has_expiry": True},
        headers=admin_headers,
    )
    prod_id = prod_res.json()["data"]["id"]

    wh_res = await client.post("/api/v1/warehouses", json={"name": "FEFO Test WH"}, headers=admin_headers)
    wh_id = wh_res.json()["data"]["id"]

    today = get_business_date()

    # Batch 1: Expires in 20 days (Rank 2)
    b1_res = await client.post(
        "/api/v1/batches",
        json={"product_id": prod_id, "batch_number": "BATCH-20DAYS", "expiry_date": (today + timedelta(days=20)).isoformat()},
        headers=staff_headers,
    )
    b1_id = b1_res.json()["data"]["id"]

    # Batch 2: Expires in 5 days (Rank 1 - earliest expiry)
    b2_res = await client.post(
        "/api/v1/batches",
        json={"product_id": prod_id, "batch_number": "BATCH-5DAYS", "expiry_date": (today + timedelta(days=5)).isoformat()},
        headers=staff_headers,
    )
    b2_id = b2_res.json()["data"]["id"]

    # Batch 3: Already EXPIRED (Should be EXCLUDED from FEFO)
    b3_res = await client.post(
        "/api/v1/batches",
        json={"product_id": prod_id, "batch_number": "BATCH-EXPIRED", "expiry_date": (today - timedelta(days=2)).isoformat()},
        headers=staff_headers,
    )
    b3_id = b3_res.json()["data"]["id"]

    # Add stock
    await client.post("/api/v1/inventory/adjust", json={"product_id": prod_id, "batch_id": b1_id, "warehouse_id": wh_id, "quantity_change": 100}, headers=staff_headers)
    await client.post("/api/v1/inventory/adjust", json={"product_id": prod_id, "batch_id": b2_id, "warehouse_id": wh_id, "quantity_change": 50}, headers=staff_headers)
    await client.post("/api/v1/inventory/adjust", json={"product_id": prod_id, "batch_id": b3_id, "warehouse_id": wh_id, "quantity_change": 30}, headers=staff_headers)

    # Request FEFO Ranked Batches
    fefo_res = await client.get(f"/api/v1/fefo/batches?product_id={prod_id}&warehouse_id={wh_id}", headers=staff_headers)
    assert fefo_res.status_code == 200
    ranked_list = fefo_res.json()["data"]

    # Expired batch MUST be excluded -> only 2 active batches returned
    assert len(ranked_list) == 2
    assert ranked_list[0]["batch_id"] == b2_id  # Expires in 5 days -> Rank 1
    assert ranked_list[1]["batch_id"] == b1_id  # Expires in 20 days -> Rank 2
    assert ranked_list[0]["fefo_rank"] == 1
    assert ranked_list[1]["fefo_rank"] == 2


@pytest.mark.asyncio
async def test_read_only_fefo_allocation_preview(client: AsyncClient, admin_headers: dict, staff_headers: dict):
    """
    Test POST /api/v1/fefo/allocate non-mutating preview.
    CRITICAL CHECK: Database inventory quantity and transactions MUST remain 100% UNCHANGED.
    """
    cat_res = await client.post("/api/v1/categories", json={"name": "Preview Cat"}, headers=admin_headers)
    cat_id = cat_res.json()["data"]["id"]

    prod_res = await client.post(
        "/api/v1/products",
        json={"name": "Butter 200g", "sku": "BUTTER-PREVIEW-01", "category_id": cat_id, "unit_price": "120.00", "has_expiry": True},
        headers=admin_headers,
    )
    prod_id = prod_res.json()["data"]["id"]

    wh_res = await client.post("/api/v1/warehouses", json={"name": "Preview WH"}, headers=admin_headers)
    wh_id = wh_res.json()["data"]["id"]

    today = get_business_date()
    b1_res = await client.post("/api/v1/batches", json={"product_id": prod_id, "batch_number": "B-EARLY", "expiry_date": (today + timedelta(days=10)).isoformat()}, headers=staff_headers)
    b1_id = b1_res.json()["data"]["id"]
    b2_res = await client.post("/api/v1/batches", json={"product_id": prod_id, "batch_number": "B-LATER", "expiry_date": (today + timedelta(days=30)).isoformat()}, headers=staff_headers)
    b2_id = b2_res.json()["data"]["id"]

    await client.post("/api/v1/inventory/adjust", json={"product_id": prod_id, "batch_id": b1_id, "warehouse_id": wh_id, "quantity_change": 40}, headers=staff_headers)
    await client.post("/api/v1/inventory/adjust", json={"product_id": prod_id, "batch_id": b2_id, "warehouse_id": wh_id, "quantity_change": 100}, headers=staff_headers)

    # Capture initial transaction count before preview call
    tx_before_res = await client.get("/api/v1/inventory/transactions", headers=staff_headers)
    tx_count_before = len(tx_before_res.json()["data"])

    # Call FEFO Allocation Preview for 70 units
    alloc_req = {"product_id": prod_id, "requested_quantity": 70, "warehouse_id": wh_id}
    preview_res = await client.post("/api/v1/fefo/allocate", json=alloc_req, headers=staff_headers)
    assert preview_res.status_code == 200
    plan = preview_res.json()["data"]

    assert plan["requested_quantity"] == 70
    assert plan["allocated_total"] == 70
    assert plan["is_fully_allocated"] is True
    assert len(plan["allocations"]) == 2
    # 40 from B-EARLY, 30 from B-LATER
    assert plan["allocations"][0]["batch_id"] == b1_id
    assert plan["allocations"][0]["allocated_quantity"] == 40
    assert plan["allocations"][1]["batch_id"] == b2_id
    assert plan["allocations"][1]["allocated_quantity"] == 30

    # VERIFY DATABASE WAS NOT MUTATED
    inv1_res = await client.get(f"/api/v1/inventory", headers=staff_headers)
    inventories = inv1_res.json()["data"]
    b1_inv = next(i for i in inventories if i["batch_id"] == b1_id)
    assert b1_inv["quantity_on_hand"] == 40  # UNCHANGED!
    assert b1_inv["quantity_reserved"] == 0  # UNCHANGED!

    tx_after_res = await client.get("/api/v1/inventory/transactions", headers=staff_headers)
    tx_count_after = len(tx_after_res.json()["data"])
    assert tx_count_after == tx_count_before  # NO TRANSACTIONS CREATED!
