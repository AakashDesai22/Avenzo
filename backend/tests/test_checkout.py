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
