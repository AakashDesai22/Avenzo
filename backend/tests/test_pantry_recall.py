"""
AVENZO Backend — Phase 10F Pantry Synchronization & Batch Recall Intelligence Tests
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.core.date_utils import get_business_date
from app.models.user import User
from app.models.product import Product, Category
from app.models.inventory import Batch, Inventory
from app.models.warehouse import Warehouse
from app.models.order import Order, OrderItem
from app.models.order_allocation import OrderBatchAllocation
from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.models.notification import NotificationRecord
from app.schemas.recall import BatchRecallRequest
from app.services import fulfillment_service, recall_service, pantry_service
from tests.conftest import _create_test_user_with_role


async def _setup_recall_env(db_session: AsyncSession):
    """Helper to set up test consumer, admin, product, warehouse, batch, and inventory."""
    uid = uuid4().hex[:8]
    consumer = await _create_test_user_with_role(db_session, f"consumer_{uid}@avenzo.dev", "CONSUMER")
    admin = await _create_test_user_with_role(db_session, f"admin_{uid}@avenzo.dev", "ADMIN")

    cat = Category(name=f"Recall Category {uid}")
    db_session.add(cat)
    await db_session.commit()

    product = Product(
        name=f"Recall Test Product {uid}",
        sku=f"RECALL-SKU-{uid}",
        category_id=cat.id,
        unit_price=Decimal("10.00"),
        has_expiry=True,
        is_active=True,
    )
    wh = Warehouse(name=f"Recall Warehouse {uid}", city="Austin")
    db_session.add_all([product, wh])
    await db_session.commit()

    batch = Batch(
        product_id=product.id,
        batch_number=f"B-RECALL-{uid}",
        expiry_date=get_business_date() + timedelta(days=30),
        status="active",
    )
    db_session.add(batch)
    await db_session.commit()

    inv = Inventory(
        product_id=product.id,
        batch_id=batch.id,
        warehouse_id=wh.id,
        quantity_on_hand=100,
        quantity_reserved=0,
    )
    db_session.add(inv)
    await db_session.commit()

    return consumer, admin, product, batch, inv, wh


@pytest.mark.asyncio
async def test_deliver_order_creates_synced_pantry_items(db_session: AsyncSession):
    """1. Test that deliver_order synchronously creates consumer PantryItems from exact allocations."""
    consumer, admin, product, batch, inv, wh = await _setup_recall_env(db_session)

    order = Order(
        order_number=f"ORD-{uuid4().hex[:8]}",
        user_id=consumer.id,
        status="CONFIRMED",
        payment_status="PAID",
        payment_method="CARD",
        subtotal=Decimal("100.00"),
        delivery_fee=Decimal("2.50"),
        total_amount=Decimal("102.50"),
        shipping_address="123 Main St, Austin, TX",
    )
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=5,
        unit_price=Decimal("20.00"),
        total_price=Decimal("100.00"),
        fulfillment_status="ALLOCATED",
    )
    db_session.add(item)
    await db_session.flush()

    alloc = OrderBatchAllocation(
        order_item_id=item.id,
        order_id=order.id,
        product_id=product.id,
        batch_id=batch.id,
        inventory_id=inv.id,
        allocated_quantity=5,
    )
    db_session.add(alloc)

    order.status = "ALLOCATED"
    await db_session.commit()

    consumer_id = consumer.id
    order_id = order.id
    item_id = item.id
    batch_id = batch.id

    await fulfillment_service.pack_order(db_session, order_id)
    await fulfillment_service.dispatch_order(db_session, order_id)

    delivered_res = await fulfillment_service.deliver_order(db_session, order_id)
    assert delivered_res.status == "DELIVERED"

    pantry_items = await pantry_service.list_pantry_items(db_session, user_id=consumer_id)
    matched = [pi for pi in pantry_items if pi.order_item_id == item_id]
    assert len(matched) == 1
    assert matched[0].batch_id == batch_id
    assert matched[0].quantity == Decimal("5.00")
    assert matched[0].is_recalled is False


@pytest.mark.asyncio
async def test_deliver_order_split_batches_creates_separate_pantry_items(db_session: AsyncSession):
    """2. Test that a multi-batch allocation creates separate PantryItems per batch."""
    consumer, admin, product, batch1, inv1, wh = await _setup_recall_env(db_session)

    batch2 = Batch(
        product_id=product.id,
        batch_number=f"BATCH-SPLIT-{uuid4().hex[:6]}",
        expiry_date=get_business_date() + timedelta(days=60),
        initial_quantity=50,
        status="active",
    )
    db_session.add(batch2)
    await db_session.flush()

    inv2 = Inventory(
        warehouse_id=wh.id,
        product_id=product.id,
        batch_id=batch2.id,
        quantity_on_hand=50,
        quantity_reserved=0,
    )
    db_session.add(inv2)
    await db_session.commit()

    order = Order(
        order_number=f"ORD-SPLIT-{uuid4().hex[:6]}",
        user_id=consumer.id,
        status="SHIPPED",
        payment_status="PAID",
        payment_method="CARD",
        subtotal=Decimal("200.00"),
        delivery_fee=Decimal("2.50"),
        total_amount=Decimal("202.50"),
        shipping_address="123 Main St, Austin, TX",
    )
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=25,
        unit_price=Decimal("8.00"),
        total_price=Decimal("200.00"),
        fulfillment_status="SHIPPED",
    )
    db_session.add(item)
    await db_session.flush()

    alloc1 = OrderBatchAllocation(
        order_item_id=item.id,
        order_id=order.id,
        product_id=product.id,
        batch_id=batch1.id,
        inventory_id=inv1.id,
        allocated_quantity=10,
    )
    alloc2 = OrderBatchAllocation(
        order_item_id=item.id,
        order_id=order.id,
        product_id=product.id,
        batch_id=batch2.id,
        inventory_id=inv2.id,
        allocated_quantity=15,
    )
    db_session.add_all([alloc1, alloc2])
    await db_session.commit()

    await fulfillment_service.deliver_order(db_session, order.id)

    pantry_items = await pantry_service.list_pantry_items(db_session, user_id=consumer.id)
    split_items = [pi for pi in pantry_items if pi.order_item_id == item.id]

    assert len(split_items) == 2
    b_ids = {pi.batch_id for pi in split_items}
    assert batch1.id in b_ids
    assert batch2.id in b_ids


@pytest.mark.asyncio
async def test_deliver_order_pantry_sync_is_idempotent(db_session: AsyncSession):
    """3. Test that repeated delivery sync calls do not duplicate PantryItems."""
    consumer, admin, product, batch, inv, wh = await _setup_recall_env(db_session)

    order = Order(
        order_number=f"ORD-IDEM-{uuid4().hex[:6]}",
        user_id=consumer.id,
        status="SHIPPED",
        payment_status="PAID",
        payment_method="CARD",
        subtotal=Decimal("50.00"),
        delivery_fee=Decimal("2.50"),
        total_amount=Decimal("52.50"),
        shipping_address="123 Main St, Austin, TX",
    )
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=2,
        unit_price=Decimal("25.00"),
        total_price=Decimal("50.00"),
        fulfillment_status="SHIPPED",
    )
    db_session.add(item)
    await db_session.flush()

    alloc = OrderBatchAllocation(
        order_item_id=item.id,
        order_id=order.id,
        product_id=product.id,
        batch_id=batch.id,
        inventory_id=inv.id,
        allocated_quantity=2,
    )
    db_session.add(alloc)
    await db_session.commit()

    await fulfillment_service.deliver_order(db_session, order.id)

    # Re-run deliver_order with status set back to SHIPPED
    order.status = "SHIPPED"
    await db_session.commit()

    await fulfillment_service.deliver_order(db_session, order.id)

    pantry_items = await pantry_service.list_pantry_items(db_session, user_id=consumer.id)
    matched = [pi for pi in pantry_items if pi.order_item_id == item.id]
    assert len(matched) == 1


@pytest.mark.asyncio
async def test_batch_recall_identifies_exact_delivered_consumers(db_session: AsyncSession):
    """7. Test batch recall marks pantry items and returns impact summary for exact delivered consumers."""
    consumer, admin, product, batch, inv, wh = await _setup_recall_env(db_session)

    order = Order(
        order_number=f"ORD-RECALL-{uuid4().hex[:6]}",
        user_id=consumer.id,
        status="SHIPPED",
        payment_status="PAID",
        payment_method="CARD",
        subtotal=Decimal("100.00"),
        delivery_fee=Decimal("2.50"),
        total_amount=Decimal("102.50"),
        shipping_address="123 Main St, Austin, TX",
    )
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=4,
        unit_price=Decimal("25.00"),
        total_price=Decimal("100.00"),
        fulfillment_status="SHIPPED",
    )
    db_session.add(item)
    await db_session.flush()

    alloc = OrderBatchAllocation(
        order_item_id=item.id,
        order_id=order.id,
        product_id=product.id,
        batch_id=batch.id,
        inventory_id=inv.id,
        allocated_quantity=4,
    )
    db_session.add(alloc)
    await db_session.commit()

    await fulfillment_service.deliver_order(db_session, order.id)

    # Execute Recall
    req = BatchRecallRequest(recall_reason="Bacterial contamination in factory line", severity="HIGH")
    impact = await recall_service.recall_batch(db_session, batch.id, user_id=admin.id, data=req)

    assert impact.affected_orders_count == 1
    assert impact.affected_consumers_count == 1
    assert impact.affected_pantry_items_count == 1
    assert impact.notifications_sent_count == 1
    assert impact.is_already_recalled is False

    pantry_items = await pantry_service.list_pantry_items(db_session, user_id=consumer.id)
    recalled_item = next(pi for pi in pantry_items if pi.order_item_id == item.id)
    assert recalled_item.is_recalled is True
    assert recalled_item.recall_reason == "Bacterial contamination in factory line"


@pytest.mark.asyncio
async def test_repeated_batch_recall_is_idempotent(db_session: AsyncSession):
    """11. Test that calling recall twice returns idempotent result and does not duplicate notifications."""
    consumer, admin, product, batch, inv, wh = await _setup_recall_env(db_session)

    req = BatchRecallRequest(recall_reason="Repeat recall test", severity="HIGH")
    impact1 = await recall_service.recall_batch(db_session, batch.id, user_id=admin.id, data=req)

    impact2 = await recall_service.recall_batch(db_session, batch.id, user_id=admin.id, data=req)
    assert impact2.is_already_recalled is True
    assert impact2.notifications_sent_count == 0


@pytest.mark.asyncio
async def test_recalled_consumed_item_retains_consumed_status(db_session: AsyncSession):
    """16. Test that a consumed pantry item keeps status='consumed' when its batch is recalled."""
    consumer, admin, product, batch, inv, wh = await _setup_recall_env(db_session)

    order = Order(
        order_number=f"ORD-CONS-{uuid4().hex[:6]}",
        user_id=consumer.id,
        status="SHIPPED",
        payment_status="PAID",
        payment_method="CARD",
        subtotal=Decimal("50.00"),
        delivery_fee=Decimal("2.50"),
        total_amount=Decimal("52.50"),
        shipping_address="123 Main St, Austin, TX",
    )
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=1,
        unit_price=Decimal("50.00"),
        total_price=Decimal("50.00"),
        fulfillment_status="SHIPPED",
    )
    db_session.add(item)
    await db_session.flush()

    alloc = OrderBatchAllocation(
        order_item_id=item.id,
        order_id=order.id,
        product_id=product.id,
        batch_id=batch.id,
        inventory_id=inv.id,
        allocated_quantity=1,
    )
    db_session.add(alloc)
    await db_session.commit()

    await fulfillment_service.deliver_order(db_session, order.id)

    pantry_items = await pantry_service.list_pantry_items(db_session, user_id=consumer.id)
    pi = next(it for it in pantry_items if it.order_item_id == item.id)

    # Consume item
    await pantry_service.consume_pantry_item(db_session, user_id=consumer.id, item_id=pi.id, consume_qty=Decimal("1.0"))

    # Recall Batch
    req = BatchRecallRequest(recall_reason="Health hazard", severity="CRITICAL")
    await recall_service.recall_batch(db_session, batch.id, user_id=admin.id, data=req)

    stmt = select(PantryItem).where(PantryItem.id == pi.id)
    res = await db_session.execute(stmt)
    db_item = res.scalars().first()

    assert db_item.status == "consumed"
    assert db_item.is_recalled is True
