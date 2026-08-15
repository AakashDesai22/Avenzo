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
