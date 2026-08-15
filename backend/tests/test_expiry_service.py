"""
AVENZO Backend — Expiry Intelligence Service Test Suite
Tests DTE calculation, expiry classification, threshold boundaries, non-expiry product handling, and risk metrics.
"""

import pytest
from datetime import timedelta
from httpx import AsyncClient
from app.core.date_utils import get_business_date
from app.services.expiry_service import calculate_dte, classify_expiry_status


def test_calculate_dte():
    """Test Days-To-Expiry calculation relative to business date."""
    today = get_business_date()
    future_date = today + timedelta(days=10)
    past_date = today - timedelta(days=5)

    assert calculate_dte(future_date, target_date=today) == 10
    assert calculate_dte(past_date, target_date=today) == -5
    assert calculate_dte(None) is None


def test_expiry_classification_boundaries():
    """Test boundary conditions for SAFE, EXPIRING_SOON, CRITICAL, EXPIRED, and N/A."""
    today = get_business_date()

    # DTE > 30 -> SAFE
    safe_date = today + timedelta(days=35)
    assert classify_expiry_status(safe_date, has_expiry=True, target_date=today) == "SAFE"

    # DTE = 30 -> EXPIRING_SOON
    boundary_30 = today + timedelta(days=30)
    assert classify_expiry_status(boundary_30, has_expiry=True, target_date=today) == "EXPIRING_SOON"

    # 7 < DTE <= 30 -> EXPIRING_SOON
    exp_soon_date = today + timedelta(days=15)
    assert classify_expiry_status(exp_soon_date, has_expiry=True, target_date=today) == "EXPIRING_SOON"

    # DTE = 7 -> CRITICAL
    boundary_7 = today + timedelta(days=7)
    assert classify_expiry_status(boundary_7, has_expiry=True, target_date=today) == "CRITICAL"

    # 0 <= DTE <= 7 -> CRITICAL
    critical_date = today + timedelta(days=3)
    assert classify_expiry_status(critical_date, has_expiry=True, target_date=today) == "CRITICAL"

    # DTE = 0 -> CRITICAL
    boundary_0 = today
    assert classify_expiry_status(boundary_0, has_expiry=True, target_date=today) == "CRITICAL"

    # DTE < 0 -> EXPIRED
    expired_date = today - timedelta(days=1)
    assert classify_expiry_status(expired_date, has_expiry=True, target_date=today) == "EXPIRED"

    # Product with has_expiry == False -> MUST return 'N/A'
    assert classify_expiry_status(safe_date, has_expiry=False, target_date=today) == "N/A"
    assert classify_expiry_status(expired_date, has_expiry=False, target_date=today) == "N/A"


@pytest.mark.asyncio
async def test_expiry_summary_and_risk_metrics_api(client: AsyncClient, admin_headers: dict, staff_headers: dict):
    """Test expiry summary aggregates and risk metrics calculation APIs."""
    # Setup Category + Products (Expiry and Non-Expiry)
    cat_res = await client.post("/api/v1/categories", json={"name": "Risk Metrics Cat"}, headers=admin_headers)
    cat_id = cat_res.json()["data"]["id"]

    # Product with Expiry
    prod1_res = await client.post(
        "/api/v1/products",
        json={"name": "Yogurt 500g", "sku": "YOGURT-RISK-01", "category_id": cat_id, "unit_price": "100.00", "cost_price": "70.00", "has_expiry": True},
        headers=admin_headers,
    )
    p1_id = prod1_res.json()["data"]["id"]

    # Product WITHOUT Expiry
    prod2_res = await client.post(
        "/api/v1/products",
        json={"name": "Steel Spoon", "sku": "SPOON-NOEXP-01", "category_id": cat_id, "unit_price": "50.00", "cost_price": "20.00", "has_expiry": False},
        headers=admin_headers,
    )
    p2_id = prod2_res.json()["data"]["id"]

    wh_res = await client.post("/api/v1/warehouses", json={"name": "Risk Metrics WH"}, headers=admin_headers)
    wh_id = wh_res.json()["data"]["id"]

    today = get_business_date()
    exp_soon_date = (today + timedelta(days=10)).isoformat()

    batch_res = await client.post(
        "/api/v1/batches",
        json={"product_id": p1_id, "batch_number": "BATCH-YOG-01", "expiry_date": exp_soon_date},
        headers=staff_headers,
    )
    b1_id = batch_res.json()["data"]["id"]

    # Add stock for expiry product
    await client.post(
        "/api/v1/inventory/adjust",
        json={"product_id": p1_id, "batch_id": b1_id, "warehouse_id": wh_id, "quantity_change": 50, "transaction_type": "RECEIPT"},
        headers=staff_headers,
    )

    # Fetch Expiry Summary
    sum_res = await client.get(f"/api/v1/inventory/expiry-summary?warehouse_id={wh_id}", headers=staff_headers)
    assert sum_res.status_code == 200
    sum_data = sum_res.json()["data"]
    assert sum_data["expiring_soon_quantity"] == 50

    # Fetch Risk Metrics
    risk_res = await client.get(f"/api/v1/inventory/risk-metrics?warehouse_id={wh_id}", headers=admin_headers)
    assert risk_res.status_code == 200
    risk_data = risk_res.json()["data"]
    assert risk_data["near_expiry_quantity"] == 50
    # capital_exposure_at_risk = 50 * 70.00 = 3500.00
    assert float(risk_data["capital_exposure_at_risk"]) == 3500.00
    # potential_sales_exposure = 50 * 100.00 = 5000.00
    assert float(risk_data["potential_sales_exposure"]) == 5000.00
