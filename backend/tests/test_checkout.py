"""
AVENZO Backend — Phase 10B Consumer Checkout Engine Test Suite
Verifies atomic checkout execution, price snapshotting, subtotal & delivery fee rules,
stock reservation increments, transaction audit logging, idempotency deduplication,
error rollbacks, and concurrency locking.
"""

import pytest
import asyncio
from datetime import timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.date_utils import get_business_date
from app.models.product import Product, Category
from app.models.inventory import Inventory, Batch, InventoryTransaction
from app.models.warehouse import Warehouse
from app.models.order import Order, OrderItem
from app.models.cart import Cart
from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.core.security import create_access_token
from tests.conftest import _create_test_user_with_role


@pytest.mark.asyncio
async def test_checkout_unauthenticated_rejected(client: AsyncClient):
    """Unauthenticated requests to checkout endpoint should return 401/403."""
    res = await client.post("/api/v1/orders", json={"shipping_address": "123 Main St"})
    assert res.status_code in (401, 403)


@pytest.mark.asyncio
async def test_checkout_empty_cart_fails(client: AsyncClient, consumer_headers: dict):
    """Attempting to checkout an empty cart returns 400 Bad Request."""
    # Ensure empty cart
    await client.delete("/api/v1/cart", headers=consumer_headers)

    res = await client.post(
        "/api/v1/orders",
        json={"shipping_address": "123 Main St, Austin TX", "payment_method": "MOCK_PAYMENT"},
        headers=consumer_headers,
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_checkout_successful_flow_and_reservation(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Successful checkout converts cart, creates order, snapshots prices, and reserves stock."""
    today = get_business_date()

    cat = Category(name="Checkout Test Cat")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Organic Almonds 500g",
        sku="CHK-NUT-001",
        category_id=cat.id,
        unit_price=Decimal("12.00"),
        cost_price=Decimal("7.00"),
        has_expiry=True,
        is_active=True,
    )
    wh = Warehouse(name="Austin Warehouse", city="Austin")
    db_session.add_all([product, wh])
    await db_session.commit()

    batch = Batch(
        product_id=product.id,
        batch_number="B-ALMOND-01",
        expiry_date=today + timedelta(days=30),
        status="active",
    )
    db_session.add(batch)
    await db_session.commit()

    inventory = Inventory(
        product_id=product.id,
        batch_id=batch.id,
        warehouse_id=wh.id,
        quantity_on_hand=50,
        quantity_reserved=0,
    )
    db_session.add(inventory)
    await db_session.commit()

    # Add 3 units to cart -> subtotal = $36.00 (< $50.00 -> $5.00 delivery fee -> total = $41.00)
    await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 3}, headers=consumer_headers
    )

    checkout_payload = {
        "shipping_address": "789 Commerce Way, Suite 400, Austin TX 78701",
        "notes": "Please leave at front gate.",
        "payment_method": "MOCK_PAYMENT",
    }
    res = await client.post("/api/v1/orders", json=checkout_payload, headers=consumer_headers)
    assert res.status_code == 201
    order_data = res.json()["data"]

    assert order_data["status"] == "PENDING"
    assert order_data["payment_status"] == "PAID"
    assert order_data["payment_method"] == "MOCK_PAYMENT"
    assert order_data["subtotal"] == "36.00"
    assert order_data["delivery_fee"] == "5.00"
    assert order_data["total_amount"] == "41.00"
    assert len(order_data["items"]) == 1

    item = order_data["items"][0]
    assert item["product_id"] == str(product.id)
    assert item["quantity"] == 3
    assert item["unit_price"] == "12.00" # Price snapshot
    assert item["total_price"] == "36.00"

    # Verify inventory reservation increment (quantity_on_hand untouched = 50, quantity_reserved = 3)
    await db_session.refresh(inventory)
    assert inventory.quantity_on_hand == 50
    assert inventory.quantity_reserved == 3
    assert inventory.quantity_available == 47

    # Verify InventoryTransaction audit record created
    tx_res = await db_session.execute(
        select(InventoryTransaction).where(
            InventoryTransaction.inventory_id == inventory.id,
            InventoryTransaction.transaction_type == "RESERVATION",
        )
    )
    tx = tx_res.scalars().first()
    assert tx is not None
    assert tx.quantity_change == 3
    assert tx.quantity_after == 3
    assert tx.reference_type == "ORDER"

    # Verify cart status is CONVERTED
    cart_res = await client.get("/api/v1/cart", headers=consumer_headers)
    assert cart_res.status_code == 200
    assert cart_res.json()["data"]["total_items_count"] == 0


@pytest.mark.asyncio
async def test_checkout_free_delivery_above_threshold(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Subtotal >= $50.00 qualifies for free delivery ($0.00 delivery fee)."""
    today = get_business_date()

    cat = Category(name="Free Delivery Cat")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Premium Extra Virgin Olive Oil 1L",
        sku="EVOO-001",
        category_id=cat.id,
        unit_price=Decimal("25.00"),
        has_expiry=True,
        is_active=True,
    )
    wh = Warehouse(name="Olive Oil Depot", city="Dallas")
    db_session.add_all([product, wh])
    await db_session.commit()

    batch = Batch(
        product_id=product.id,
        batch_number="B-OIL-100",
        expiry_date=today + timedelta(days=120),
        status="active",
    )
    db_session.add(batch)
    await db_session.commit()

    inventory = Inventory(
        product_id=product.id,
        batch_id=batch.id,
        warehouse_id=wh.id,
        quantity_on_hand=20,
        quantity_reserved=0,
    )
    db_session.add(inventory)
    await db_session.commit()

    # Clear old cart items and add 3 units -> subtotal $75.00 >= $50.00
    await client.delete("/api/v1/cart", headers=consumer_headers)
    await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 3}, headers=consumer_headers
    )

    res = await client.post(
        "/api/v1/orders",
        json={"shipping_address": "100 Olive St, Dallas TX", "payment_method": "MOCK_PAYMENT"},
        headers=consumer_headers,
    )
    assert res.status_code == 201
    order_data = res.json()["data"]
    assert order_data["subtotal"] == "75.00"
    assert order_data["delivery_fee"] == "0.00"
    assert order_data["total_amount"] == "75.00"


@pytest.mark.asyncio
async def test_checkout_insufficient_stock_fails_and_rolls_back(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Checkout fails with 400 Bad Request if requested quantity exceeds available stock."""
    today = get_business_date()

    cat = Category(name="Low Stock Cat")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Limited Edition Honey",
        sku="HNY-LOW-001",
        category_id=cat.id,
        unit_price=Decimal("15.00"),
        has_expiry=True,
        is_active=True,
    )
    wh = Warehouse(name="Honey Warehouse", city="Houston")
    db_session.add_all([product, wh])
    await db_session.commit()

    batch = Batch(
        product_id=product.id,
        batch_number="B-HNY-01",
        expiry_date=today + timedelta(days=60),
        status="active",
    )
    db_session.add(batch)
    await db_session.commit()

    # 5 on hand, 3 reserved -> ONLY 2 AVAILABLE
    inventory = Inventory(
        product_id=product.id,
        batch_id=batch.id,
        warehouse_id=wh.id,
        quantity_on_hand=5,
        quantity_reserved=3,
    )
    db_session.add(inventory)
    await db_session.commit()

    # Clear old cart items and request 4 units (> 2 available)
    await client.delete("/api/v1/cart", headers=consumer_headers)
    await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 4}, headers=consumer_headers
    )

    res = await client.post(
        "/api/v1/orders",
        json={"shipping_address": "200 Honey Blvd, Houston TX", "payment_method": "MOCK_PAYMENT"},
        headers=consumer_headers,
    )
    assert res.status_code == 400
    assert "insufficient stock" in res.json()["detail"].lower()

    # Verify inventory was NOT modified
    await db_session.refresh(inventory)
    assert inventory.quantity_reserved == 3


@pytest.mark.asyncio
async def test_checkout_idempotency_key_prevents_duplicate_orders(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Sending the same Idempotency-Key returns the existing order without duplicate stock reservation."""
    today = get_business_date()

    cat = Category(name="Idempotency Cat")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Organic Coffee Beans 1kg",
        sku="CF-IDEM-001",
        category_id=cat.id,
        unit_price=Decimal("18.00"),
        has_expiry=True,
        is_active=True,
    )
    wh = Warehouse(name="Coffee Depot", city="Seattle")
    db_session.add_all([product, wh])
    await db_session.commit()

    batch = Batch(
        product_id=product.id,
        batch_number="B-COFFEE-01",
        expiry_date=today + timedelta(days=90),
        status="active",
    )
    db_session.add(batch)
    await db_session.commit()

    inventory = Inventory(
        product_id=product.id,
        batch_id=batch.id,
        warehouse_id=wh.id,
        quantity_on_hand=100,
        quantity_reserved=0,
    )
    db_session.add(inventory)
    await db_session.commit()

    await client.delete("/api/v1/cart", headers=consumer_headers)
    await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 2}, headers=consumer_headers
    )

    idempotency_key = "idem-key-unique-test-9999"
    headers_with_idem = {**consumer_headers, "Idempotency-Key": idempotency_key}

    # First checkout
    res_1 = await client.post(
        "/api/v1/orders",
        json={"shipping_address": "500 Pike St, Seattle WA", "payment_method": "MOCK_PAYMENT"},
        headers=headers_with_idem,
    )
    assert res_1.status_code == 201
    order_1 = res_1.json()["data"]

    # Second checkout with SAME Idempotency-Key
    res_2 = await client.post(
        "/api/v1/orders",
        json={"shipping_address": "500 Pike St, Seattle WA", "payment_method": "MOCK_PAYMENT"},
        headers=headers_with_idem,
    )
    assert res_2.status_code == 201
    order_2 = res_2.json()["data"]

    # Must return EXACT SAME ORDER
    assert order_1["id"] == order_2["id"]
    assert order_1["order_number"] == order_2["order_number"]

    # Verify inventory was ONLY reserved ONCE (2 units reserved)
    await db_session.refresh(inventory)
    assert inventory.quantity_reserved == 2


@pytest.mark.asyncio
async def test_demo_purchase_atomic_flow_fefo_and_pantry_sync(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """
    Demo purchase atomically executes:
    1. Validates published status and prices
    2. FEFO allocation across multiple batches (earliest-expiring batch first)
    3. Physical warehouse stock deduction (quantity_on_hand -= qty) and SALE audit log
    4. Synchronous creation of distinct PantryItem records for each batch allocation with exact expiry dates
    5. Order status = DELIVERED, payment_status = DEMO_COMPLETED, delivery_fee = $0.00
    6. Cart converted
    """
    today = get_business_date()

    cat = Category(name="Fresh Dairy", is_active=True)
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Organic Whole Milk 1L",
        sku="CHK-MILK-DEMO-01",
        category_id=cat.id,
        unit_price=Decimal("4.50"),
        cost_price=Decimal("2.50"),
        has_expiry=True,
        is_active=True,
        is_published=True,
        unit_of_measure="bottles",
    )
    wh = Warehouse(name="Central Distribution Wh", city="Austin")
    db_session.add_all([product, wh])
    await db_session.commit()

    # Batch 1: Expires in 10 days, 10 units available (earliest expiry)
    batch_early = Batch(
        product_id=product.id,
        batch_number="BATCH-MILK-EARLY",
        expiry_date=today + timedelta(days=10),
        status="active",
    )
    # Batch 2: Expires in 30 days, 20 units available (later expiry)
    batch_later = Batch(
        product_id=product.id,
        batch_number="BATCH-MILK-LATER",
        expiry_date=today + timedelta(days=30),
        status="active",
    )
    db_session.add_all([batch_early, batch_later])
    await db_session.commit()

    inv_early = Inventory(
        product_id=product.id,
        batch_id=batch_early.id,
        warehouse_id=wh.id,
        quantity_on_hand=10,
        quantity_reserved=0,
    )
    inv_later = Inventory(
        product_id=product.id,
        batch_id=batch_later.id,
        warehouse_id=wh.id,
        quantity_on_hand=20,
        quantity_reserved=0,
    )
    db_session.add_all([inv_early, inv_later])
    await db_session.commit()

    # Dedicated consumer user for demo purchase to prevent side-effects on other analytics tests
    demo_user = await _create_test_user_with_role(db_session, "demo_purchase_consumer@avenzo.dev", "CONSUMER")
    demo_token = create_access_token(subject=str(demo_user.id), role="CONSUMER")
    demo_headers = {"Authorization": f"Bearer {demo_token}"}

    # Consumer clears cart and adds 14 units (requires 10 from early batch + 4 from later batch)
    await client.delete("/api/v1/cart", headers=demo_headers)
    add_res = await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 14}, headers=demo_headers
    )
    assert add_res.status_code == 201

    checkout_payload = {
        "shipping_address": "456 Consumer St, Austin TX",
        "notes": "Demo purchase test",
        "payment_method": "MOCK_PAYMENT",
        "demo_purchase": True,
    }
    res = await client.post("/api/v1/orders", json=checkout_payload, headers=demo_headers)
    assert res.status_code == 201
    order_data = res.json()["data"]

    # 1. Order details verified
    assert order_data["status"] == "DELIVERED"
    assert order_data["payment_status"] == "DEMO_COMPLETED"
    assert Decimal(str(order_data["delivery_fee"])) == Decimal("0.00")
    assert Decimal(str(order_data["subtotal"])) == Decimal("63.00")
    assert Decimal(str(order_data["total_amount"])) == Decimal("63.00")

    # 2. Allocations verified
    item_allocs = order_data["items"][0]["allocations"]
    assert len(item_allocs) == 2
    # First allocation: 10 units from early batch
    assert item_allocs[0]["allocated_quantity"] == 10
    assert item_allocs[0]["batch_number"] == "BATCH-MILK-EARLY"
    # Second allocation: 4 units from later batch
    assert item_allocs[1]["allocated_quantity"] == 4
    assert item_allocs[1]["batch_number"] == "BATCH-MILK-LATER"

    # 3. Warehouse stock physically deducted
    await db_session.refresh(inv_early)
    await db_session.refresh(inv_later)
    assert inv_early.quantity_on_hand == 0
    assert inv_later.quantity_on_hand == 16

    # 4. Consumer pantry items created with distinct batch expiries
    pantry_stmt = (
        select(PantryItem)
        .where(PantryItem.product_id == product.id)
        .order_by(PantryItem.expiry_date.asc())
    )
    pantry_res = await db_session.execute(pantry_stmt)
    pantry_items = pantry_res.scalars().all()
    assert len(pantry_items) == 2

    # Early batch item in pantry
    assert pantry_items[0].quantity == 10
    assert pantry_items[0].unit == "bottles"
    assert pantry_items[0].batch_id == batch_early.id
    assert pantry_items[0].expiry_date == today + timedelta(days=10)

    # Later batch item in pantry
    assert pantry_items[1].quantity == 4
    assert pantry_items[1].unit == "bottles"
    assert pantry_items[1].batch_id == batch_later.id
    assert pantry_items[1].expiry_date == today + timedelta(days=30)

    # 5. Audit logs in PantryItemLog
    for pi in pantry_items:
        log_res = await db_session.execute(
            select(PantryItemLog).where(PantryItemLog.pantry_item_id == pi.id)
        )
        logs = log_res.scalars().all()
        assert len(logs) == 1
        assert logs[0].action == "SYNCED_FROM_ORDER"


@pytest.mark.asyncio
async def test_demo_purchase_draft_product_rejected(
    client: AsyncClient, db_session: AsyncSession, consumer_headers: dict
):
    """Demo purchase strictly rejects unpublished (draft) products."""
    today = get_business_date()
    cat = Category(name="Draft Category", is_active=True)
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name="Unpublished Snack Bar",
        sku="CHK-DRAFT-001",
        category_id=cat.id,
        unit_price=Decimal("3.00"),
        has_expiry=False,
        is_active=True,
        is_published=False,  # DRAFT!
    )
    wh = Warehouse(name="Austin Warehouse Draft", city="Austin")
    db_session.add_all([product, wh])
    await db_session.commit()

    batch = Batch(product_id=product.id, batch_number="B-DRAFT-01", status="active")
    db_session.add(batch)
    await db_session.commit()

    inv = Inventory(product_id=product.id, batch_id=batch.id, warehouse_id=wh.id, quantity_on_hand=50)
    db_session.add(inv)
    await db_session.commit()

    await client.delete("/api/v1/cart", headers=consumer_headers)
    await client.post(
        "/api/v1/cart/items", json={"product_id": str(product.id), "quantity": 1}, headers=consumer_headers
    )

    res = await client.post(
        "/api/v1/orders",
        json={"shipping_address": "123 Test Rd", "demo_purchase": True},
        headers=consumer_headers,
    )
    assert res.status_code == 400
    assert "draft" in res.json()["detail"].lower()

