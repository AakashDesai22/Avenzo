"""
AVENZO Backend — Consumer Digital Pantry API & Service Tests
Comprehensive test coverage for Phase 5A Consumer Digital Pantry functionality,
expiry calculations, consume/discard actions, audit logs, and strict consumer data isolation.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID as PyUUID
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.models.product import Category, Product
from app.models.inventory import Batch


@pytest.mark.asyncio
async def test_pantry_item_crud_and_ownership_isolation(
    client: AsyncClient,
    consumer_headers: dict,
    staff_headers: dict,
    db_session: AsyncSession,
):
    """
    Tests full CRUD lifecycle for consumer pantry item and verifies strict
    consumer ownership isolation (rejects cross-consumer access).
    """
    # 1. Add item to Consumer Pantry via POST /api/v1/pantry
    payload = {
        "custom_name": "Organic Milk 1L",
        "quantity": "2.0",
        "unit": "liters",
        "storage_location": "fridge",
        "purchase_date": date.today().isoformat(),
        "expiry_date": (date.today() + timedelta(days=15)).isoformat(),
        "notes": "Keep refrigerated",
    }
    response = await client.post("/api/v1/pantry", json=payload, headers=consumer_headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    item_data = res_data["data"]
    item_id = item_data["id"]

    assert item_data["custom_name"] == "Organic Milk 1L"
    assert Decimal(str(item_data["quantity"])) == Decimal("2.0")
    assert item_data["storage_location"] == "fridge"
    assert item_data["status"] == "active"
    assert item_data["days_to_expiry"] == 15
    assert item_data["expiry_status"] == "EXPIRING_SOON"

    # Verify ADDED audit log recorded
    from uuid import UUID as PyUUID
    log_res = await db_session.execute(
        select(PantryItemLog).where(PantryItemLog.pantry_item_id == PyUUID(item_id))
    )
    logs = log_res.scalars().all()
    assert len(logs) == 1
    assert logs[0].action == "ADDED"
    assert Decimal(str(logs[0].quantity_change)) == Decimal("2.0")

    # 2. Retrieve pantry item via GET /api/v1/pantry/{id} as owner
    get_res = await client.get(f"/api/v1/pantry/{item_id}", headers=consumer_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == item_id

    # 3. Cross-Consumer Access Rejection: Another user attempting access gets 404
    cross_res = await client.get(f"/api/v1/pantry/{item_id}", headers=staff_headers)
    assert cross_res.status_code == 404

    # 4. List pantry items via GET /api/v1/pantry
    list_res = await client.get("/api/v1/pantry", headers=consumer_headers)
    assert list_res.status_code == 200
    items = list_res.json()["data"]
    assert len(items) >= 1
    assert any(i["id"] == item_id for i in items)

    # 5. Update pantry item via PUT /api/v1/pantry/{id}
    update_payload = {
        "notes": "Updated note: consume before weekend",
        "quantity": "3.5",
    }
    update_res = await client.put(f"/api/v1/pantry/{item_id}", json=update_payload, headers=consumer_headers)
    assert update_res.status_code == 200
    assert Decimal(str(update_res.json()["data"]["quantity"])) == Decimal("3.5")
    assert update_res.json()["data"]["notes"] == "Updated note: consume before weekend"

    # Verify QUANTITY_ADJUSTED log
    log_res2 = await db_session.execute(
        select(PantryItemLog).where(PantryItemLog.pantry_item_id == PyUUID(item_id), PantryItemLog.action == "QUANTITY_ADJUSTED")
    )
    adj_logs = log_res2.scalars().all()
    assert len(adj_logs) == 1
    assert Decimal(str(adj_logs[0].quantity_change)) == Decimal("1.5") # 3.5 - 2.0 = +1.5

    # 6. Soft delete via DELETE /api/v1/pantry/{id}
    del_res = await client.delete(f"/api/v1/pantry/{item_id}", headers=consumer_headers)
    assert del_res.status_code == 200

    # Verify soft deleted item no longer returned in active list
    list_after_del = await client.get("/api/v1/pantry", headers=consumer_headers)
    assert not any(i["id"] == item_id for i in list_after_del.json()["data"])


@pytest.mark.asyncio
async def test_consume_pantry_item_flow(
    client: AsyncClient,
    consumer_headers: dict,
    db_session: AsyncSession,
):
    """
    Tests partial and full item consumption, quantity validation, and status transitions.
    """
    # Create item with quantity 5.0
    payload = {
        "custom_name": "Greek Yogurt Pack",
        "quantity": "5.0",
        "unit": "cups",
        "storage_location": "fridge",
    }
    create_res = await client.post("/api/v1/pantry", json=payload, headers=consumer_headers)
    item_id = create_res.json()["data"]["id"]

    # 1. Over-consumption rejection: attempting to consume 10.0 from 5.0 stock
    over_res = await client.post(
        f"/api/v1/pantry/{item_id}/consume",
        json={"quantity": "10.0"},
        headers=consumer_headers,
    )
    assert over_res.status_code == 400
    assert "Available stock is" in over_res.json()["detail"]

    # 2. Invalid quantity rejection: consuming 0 or negative
    zero_res = await client.post(
        f"/api/v1/pantry/{item_id}/consume",
        json={"quantity": "0.0"},
        headers=consumer_headers,
    )
    assert zero_res.status_code == 422 # Pydantic validation gt=0

    # 3. Partial Consumption: Consume 2.0 cups out of 5.0
    part_res = await client.post(
        f"/api/v1/pantry/{item_id}/consume",
        json={"quantity": "2.0"},
        headers=consumer_headers,
    )
    assert part_res.status_code == 200
    assert Decimal(str(part_res.json()["data"]["quantity"])) == Decimal("3.0")
    assert part_res.json()["data"]["status"] == "active"

    # 4. Full Consumption: Consume remaining 3.0 cups
    full_res = await client.post(
        f"/api/v1/pantry/{item_id}/consume",
        json={"quantity": "3.0"},
        headers=consumer_headers,
    )
    assert full_res.status_code == 200
    assert Decimal(str(full_res.json()["data"]["quantity"])) == Decimal("0.0")
    assert full_res.json()["data"]["status"] == "consumed"

    # Verify CONSUMED logs
    log_res = await db_session.execute(
        select(PantryItemLog).where(PantryItemLog.pantry_item_id == PyUUID(item_id), PantryItemLog.action == "CONSUMED")
    )
    consumed_logs = log_res.scalars().all()
    assert len(consumed_logs) == 2


@pytest.mark.asyncio
async def test_discard_pantry_item_flow(
    client: AsyncClient,
    consumer_headers: dict,
    db_session: AsyncSession,
):
    """
    Tests item waste/discarding action, validation, and status transitions.
    """
    payload = {
        "custom_name": "Spoiled Berries",
        "quantity": "2.0",
        "unit": "boxes",
        "storage_location": "fridge",
    }
    create_res = await client.post("/api/v1/pantry", json=payload, headers=consumer_headers)
    item_id = create_res.json()["data"]["id"]

    # Over-discard rejection
    over_res = await client.post(
        f"/api/v1/pantry/{item_id}/discard",
        json={"quantity": "3.0"},
        headers=consumer_headers,
    )
    assert over_res.status_code == 400

    # Discard full quantity
    discard_res = await client.post(
        f"/api/v1/pantry/{item_id}/discard",
        json={"quantity": "2.0"},
        headers=consumer_headers,
    )
    assert discard_res.status_code == 200
    assert Decimal(str(discard_res.json()["data"]["quantity"])) == Decimal("0.0")
    assert discard_res.json()["data"]["status"] == "discarded"

    # Verify DISCARDED log
    log_res = await db_session.execute(
        select(PantryItemLog).where(PantryItemLog.pantry_item_id == PyUUID(item_id), PantryItemLog.action == "DISCARDED")
    )
    discard_logs = log_res.scalars().all()
    assert len(discard_logs) == 1
    assert Decimal(str(discard_logs[0].quantity_change)) == Decimal("-2.0")


@pytest.mark.asyncio
async def test_expiring_pantry_items_and_dte_ordering(
    client: AsyncClient,
    consumer_headers: dict,
):
    """
    Tests GET /api/v1/pantry/expiring endpoint returning items sorted by DTE ASC
    (expired items DTE < 0 appear before future expiring items).
    """
    today = date.today()

    # Item 1: Expires in 10 days (SAFE)
    await client.post("/api/v1/pantry", json={
        "custom_name": "Fresh Cheese",
        "quantity": "1",
        "expiry_date": (today + timedelta(days=10)).isoformat(),
    }, headers=consumer_headers)

    # Item 2: Expired 2 days ago (EXPIRED, DTE = -2)
    await client.post("/api/v1/pantry", json={
        "custom_name": "Old Bread",
        "quantity": "1",
        "expiry_date": (today - timedelta(days=2)).isoformat(),
    }, headers=consumer_headers)

    # Item 3: Expires in 2 days (CRITICAL, DTE = 2)
    await client.post("/api/v1/pantry", json={
        "custom_name": "Ripe Bananas",
        "quantity": "1",
        "expiry_date": (today + timedelta(days=2)).isoformat(),
    }, headers=consumer_headers)

    # Item 4: Non-expiry item (no expiry date)
    await client.post("/api/v1/pantry", json={
        "custom_name": "Table Salt",
        "quantity": "1",
    }, headers=consumer_headers)

    # Call GET /api/v1/pantry/expiring
    response = await client.get("/api/v1/pantry/expiring", headers=consumer_headers)
    assert response.status_code == 200
    expiring_items = response.json()["data"]

    # Non-expiry item must not be included
    assert not any(item["custom_name"] == "Table Salt" for item in expiring_items)

    # Extract DTEs
    dtes = [item["days_to_expiry"] for item in expiring_items if item["days_to_expiry"] is not None]

    # Verify sorted ascending by DTE
    assert dtes == sorted(dtes)

    # Verify first item is Old Bread (DTE -2)
    assert expiring_items[0]["custom_name"] == "Old Bread"
    assert expiring_items[0]["expiry_status"] == "EXPIRED"


@pytest.mark.asyncio
async def test_product_and_batch_association(
    client: AsyncClient,
    consumer_headers: dict,
    db_session: AsyncSession,
):
    """
    Tests linking pantry item to Master Product and Batch entities,
    and verifying fallback shelf-life calculation.
    """
    # Create Category & Product with shelf_life_days = 14
    category = Category(name="Dairy Products")
    db_session.add(category)
    await db_session.commit()

    product = Product(
        name="Amul Butter 500g",
        sku="SKU-PANTRY-BUTTER-999",
        barcode="8909999888777",
        category_id=category.id,
        unit_price=Decimal("250.00"),
        shelf_life_days=14,
        has_expiry=True,
    )
    db_session.add(product)
    await db_session.commit()

    batch = Batch(
        product_id=product.id,
        batch_number="BATCH-BUTTER-2026",
        expiry_date=date.today() + timedelta(days=20),
    )
    db_session.add(batch)
    await db_session.commit()

    # Add pantry item linked to product_id and batch_id
    payload = {
        "product_id": str(product.id),
        "batch_id": str(batch.id),
        "quantity": "2.0",
        "storage_location": "fridge",
    }
    res = await client.post("/api/v1/pantry", json=payload, headers=consumer_headers)
    assert res.status_code == 201
    item_data = res.json()["data"]

    assert item_data["product_id"] == str(product.id)
    assert item_data["product"]["name"] == "Amul Butter 500g"
    assert item_data["batch_id"] == str(batch.id)
    assert item_data["barcode"] == "8909999888777"
    # Expiry date resolved from batch
    assert item_data["expiry_date"] == (date.today() + timedelta(days=20)).isoformat()
