"""
AVENZO Backend — Closed-Loop Waste & Utilization Analytics Test Suite
Tests consumer waste metrics, Waste Reduction Index, ownership isolation,
and aggregate privacy-safe business waste analytics.
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user import User
from app.models.product import Product, Category
from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.models.inventory import Inventory, Batch
from app.models.warehouse import Warehouse


@pytest.mark.asyncio
async def test_consumer_waste_analytics_zero_history(
    client: AsyncClient,
    consumer_headers: dict,
):
    """Test consumer analytics endpoint for user with zero pantry history."""
    res = await client.get(
        "/api/v1/analytics/consumer",
        headers=consumer_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    metrics = data["data"]
    assert metrics["total_items_tracked"] == 0
    assert metrics["has_sufficient_history"] is False
    assert metrics["waste_reduction_score"] is None
    assert "No pantry activity" in metrics["history_status"]


@pytest.mark.asyncio
async def test_consumer_waste_analytics_with_activity(
    client: AsyncClient,
    consumer_headers: dict,
    db_session: AsyncSession,
):
    """Test consumer analytics and Waste Reduction Index calculation after consume and discard actions."""
    # Fetch test consumer
    user_res = await db_session.execute(select(User).where(User.email == "consumer_test_user@avenzo.dev"))
    test_consumer = user_res.scalars().first()

    # Create category and product
    cat = Category(name="Fresh Dairy", description="Dairy products")
    db_session.add(cat)
    await db_session.flush()

    prod = Product(
        name="Organic Whole Milk",
        sku="TEST-MILK-101",
        category_id=cat.id,
        unit_price=Decimal("4.50"),
        cost_price=Decimal("2.50"),
    )
    db_session.add(prod)
    await db_session.flush()

    # Create default pantry for consumer
    pantry = ConsumerPantry(
        user_id=test_consumer.id,
        name="Test Analytics Pantry",
        is_default=True,
    )
    db_session.add(pantry)
    await db_session.flush()

    # Add 3 pantry items
    item1 = PantryItem(
        pantry_id=pantry.id,
        product_id=prod.id,
        quantity=Decimal("10.0"),
        unit="units",
        status="consumed",
    )
    item2 = PantryItem(
        pantry_id=pantry.id,
        product_id=prod.id,
        quantity=Decimal("2.0"),
        unit="units",
        status="discarded",
    )
    item3 = PantryItem(
        pantry_id=pantry.id,
        product_id=prod.id,
        quantity=Decimal("5.0"),
        unit="units",
        status="active",
    )
    db_session.add_all([item1, item2, item3])
    await db_session.flush()

    # Add logs: 10 consumed, 2 discarded
    log1 = PantryItemLog(
        pantry_item_id=item1.id,
        action="CONSUMED",
        quantity_change=Decimal("-10.0"),
    )
    log2 = PantryItemLog(
        pantry_item_id=item2.id,
        action="DISCARDED",
        quantity_change=Decimal("-2.0"),
    )
    db_session.add_all([log1, log2])
    await db_session.commit()

    # Request analytics via API
    res = await client.get(
        "/api/v1/analytics/consumer",
        headers=consumer_headers,
    )
    assert res.status_code == 200
    data = res.json()
    metrics = data["data"]

    assert metrics["total_items_tracked"] == 3
    assert metrics["total_items_consumed"] == 1
    assert metrics["total_items_discarded"] == 1
    assert metrics["consumed_quantity"] == 10.0
    assert metrics["discarded_quantity"] == 2.0
    assert metrics["has_sufficient_history"] is True

    # Consumption Ratio: 10 / 12 = 0.8333 -> 83% Score
    assert metrics["consumption_ratio"] == 0.8333
    assert metrics["waste_reduction_score"] == 83
    assert metrics["estimated_money_saved"] == 45.0


@pytest.mark.asyncio
async def test_consumer_cannot_access_business_analytics(
    client: AsyncClient,
    consumer_headers: dict,
):
    """Ensure consumer role receives HTTP 403 Forbidden when requesting business waste analytics."""
    res = await client.get(
        "/api/v1/analytics/business/waste",
        headers=consumer_headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_business_waste_analytics_privacy_and_aggregation(
    client: AsyncClient,
    admin_headers: dict,
    db_session: AsyncSession,
):
    """Test business waste analytics endpoint for ADMIN role, verifying privacy and top spoilage products."""
    cat = Category(name="Produce", description="Fresh produce")
    db_session.add(cat)
    await db_session.flush()

    prod = Product(
        name="Organic Strawberries",
        sku="TEST-STRAW-202",
        category_id=cat.id,
        unit_price=Decimal("5.00"),
        cost_price=Decimal("3.00"),
    )
    wh = Warehouse(name="Main Central Facility")
    db_session.add_all([prod, wh])
    await db_session.flush()

    batch = Batch(
        product_id=prod.id,
        batch_number="ANALYTICS-EXPIRED-01",
        initial_quantity=100,
        expiry_date=date.today() - timedelta(days=5),
        status="expired",
    )
    db_session.add(batch)
    await db_session.flush()

    inv = Inventory(
        product_id=prod.id,
        batch_id=batch.id,
        warehouse_id=wh.id,
        quantity_on_hand=50,
        quantity_reserved=0,
    )
    db_session.add(inv)
    await db_session.commit()

    # Fetch business waste analytics
    res = await client.get(
        "/api/v1/analytics/business/waste",
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    analytics = data["data"]

    assert analytics["total_warehouse_expired_units"] >= 50
    assert analytics["total_capital_lost_expired"] >= 150.0

    # Privacy Guarantee Audit: Verify no user identifying keys exist in response
    assert "user_id" not in analytics
    assert "consumer_name" not in analytics
    assert "email" not in analytics
