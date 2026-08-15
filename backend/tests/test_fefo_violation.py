"""
AVENZO Backend — FEFO Violation Detection & Audit Test Suite
"""

import pytest
from datetime import timedelta
from httpx import AsyncClient
from app.core.date_utils import get_business_date


@pytest.mark.asyncio
async def test_fefo_violation_detection_and_audit_log(client: AsyncClient, admin_headers: dict, staff_headers: dict):
    """
    Test FEFO violation detection:
    1. Selection of FEFO #1 optimal batch -> Compliant (No violation).
    2. Selection of later-expiring batch while earlier available stock exists -> Violation detected, warning issued, FEFO_VIOLATION logged in audit.
    3. Selection after earlier stock is exhausted -> Compliant (No violation).
    """
    cat_res = await client.post("/api/v1/categories", json={"name": "Violation Test Cat"}, headers=admin_headers)
    cat_id = cat_res.json()["data"]["id"]

    prod_res = await client.post(
        "/api/v1/products",
        json={"name": "Cheese Slice 200g", "sku": "CHEESE-VIOL-01", "category_id": cat_id, "unit_price": "180.00", "has_expiry": True},
        headers=admin_headers,
    )
    prod_id = prod_res.json()["data"]["id"]

    wh_res = await client.post("/api/v1/warehouses", json={"name": "Violation WH"}, headers=admin_headers)
    wh_id = wh_res.json()["data"]["id"]

    today = get_business_date()
    # Batch A: Expires in 5 days, 10 units available
    b_a_res = await client.post("/api/v1/batches", json={"product_id": prod_id, "batch_number": "BATCH-A-EARLY", "expiry_date": (today + timedelta(days=5)).isoformat()}, headers=staff_headers)
    b_a_id = b_a_res.json()["data"]["id"]

    # Batch B: Expires in 25 days, 100 units available
    b_b_res = await client.post("/api/v1/batches", json={"product_id": prod_id, "batch_number": "BATCH-B-LATER", "expiry_date": (today + timedelta(days=25)).isoformat()}, headers=staff_headers)
    b_b_id = b_b_res.json()["data"]["id"]

    await client.post("/api/v1/inventory/adjust", json={"product_id": prod_id, "batch_id": b_a_id, "warehouse_id": wh_id, "quantity_change": 10}, headers=staff_headers)
    await client.post("/api/v1/inventory/adjust", json={"product_id": prod_id, "batch_id": b_b_id, "warehouse_id": wh_id, "quantity_change": 100}, headers=staff_headers)

    # CASE 1: Compliant selection (Select Batch A)
    comp_req = {
        "product_id": prod_id,
        "selected_batch_id": b_a_id,
        "requested_quantity": 5,
        "warehouse_id": wh_id,
    }
    comp_res = await client.post("/api/v1/fefo/verify-selection", json=comp_req, headers=staff_headers)
    assert comp_res.status_code == 200
    c_data = comp_res.json()["data"]
    assert c_data["is_compliant"] is True
    assert c_data["violation_detected"] is False
    assert c_data["audit_logged"] is False

    # CASE 2: Non-compliant selection (User picks Batch B for 20 units while Batch A with 10 units exists!)
    viol_req = {
        "product_id": prod_id,
        "selected_batch_id": b_b_id,
        "requested_quantity": 20,
        "warehouse_id": wh_id,
        "override_reason": "Customer specifically requested longer expiry date",
    }
    viol_res = await client.post("/api/v1/fefo/verify-selection", json=viol_req, headers=staff_headers)
    assert viol_res.status_code == 200
    v_data = viol_res.json()["data"]
    assert v_data["is_compliant"] is False
    assert v_data["violation_detected"] is True
    assert v_data["earlier_available_batch_id"] == b_a_id
    assert v_data["bypassed_earlier_quantity"] == 10
    assert "bypasses 10 available units" in v_data["warning_message"]
    assert v_data["audit_logged"] is True

    # VERIFY AUDIT LOG TRANSACTION WAS CREATED
    tx_res = await client.get("/api/v1/inventory/transactions", headers=staff_headers)
    assert tx_res.status_code == 200
    transactions = tx_res.json()["data"]
    viol_tx = next(t for t in transactions if t["transaction_type"] == "FEFO_VIOLATION")
    assert "Customer specifically requested longer expiry date" in viol_tx["notes"]
