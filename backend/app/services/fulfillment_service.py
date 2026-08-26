"""
AVENZO Backend — Order Fulfillment & Server-Side FEFO Allocation Service
Implements strict Order state machine transitions, server-side FEFO allocation,
physical stock deduction, stock reservation releases, and batch traceability queries.
"""

from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.core.date_utils import get_business_date
from app.models.order import Order, OrderItem
from app.models.order_allocation import OrderBatchAllocation
from app.models.inventory import Inventory, Batch, InventoryTransaction
from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.models.product import Product
from app.schemas.order import OrderRead, OrderItemRead
from app.schemas.order_allocation import OrderBatchAllocationRead
from app.schemas.marketplace import MarketplaceProductRead
from app.services import fefo_service


def build_fulfillment_order_read(order: Order) -> OrderRead:
    """Helper to convert Order ORM with allocations into OrderRead response."""
    items_read: List[OrderItemRead] = []
    for item in order.items:
        prod = item.product
        prod_mkt = None
        if prod:
            prod_mkt = MarketplaceProductRead(
                id=prod.id,
                name=prod.name,
                description=prod.description,
                sku=prod.sku,
                barcode=prod.barcode,
                category_id=prod.category_id,
                category=prod.category,
                brand_id=prod.brand_id,
                brand=prod.brand,
                unit_of_measure=prod.unit_of_measure,
                unit_price=item.unit_price,
                shelf_life_days=prod.shelf_life_days,
                has_expiry=prod.has_expiry,
                image_url=prod.image_url,
                is_active=prod.is_active,
                available_quantity=0,
                is_available=True,
            )

        allocs_read: List[OrderBatchAllocationRead] = []
        for alloc in getattr(item, "allocations", []):
            allocs_read.append(
                OrderBatchAllocationRead(
                    id=alloc.id,
                    order_item_id=alloc.order_item_id,
                    order_id=alloc.order_id,
                    product_id=alloc.product_id,
                    batch_id=alloc.batch_id,
                    inventory_id=alloc.inventory_id,
                    allocated_quantity=alloc.allocated_quantity,
                    batch_number=alloc.batch.batch_number if alloc.batch else None,
                    expiry_date=alloc.batch.expiry_date if alloc.batch else None,
                    created_at=alloc.created_at,
                    updated_at=alloc.updated_at,
                )
            )

        items_read.append(
            OrderItemRead(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                fulfillment_status=item.fulfillment_status,
                product=prod_mkt,
                allocations=allocs_read,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    return OrderRead(
        id=order.id,
        order_number=order.order_number,
        user_id=order.user_id,
        status=order.status,
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        total_amount=order.total_amount,
        shipping_address=order.shipping_address,
        notes=order.notes,
        items=items_read,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


async def _get_locked_order(session: AsyncSession, order_id: UUID) -> Order:
    """Helper to fetch and row-lock Order entity."""
    stmt = (
        select(Order)
        .options(
            joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.category),
            joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.brand),
            joinedload(Order.items).joinedload(OrderItem.allocations).joinedload(OrderBatchAllocation.batch),
        )
        .where(Order.id == order_id, Order.is_deleted == False)
        .with_for_update()
    )
    res = await session.execute(stmt)
    order = res.scalars().unique().first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found.",
        )
    return order


async def confirm_order(session: AsyncSession, order_id: UUID) -> OrderRead:
    """Transitions order from PENDING -> CONFIRMED."""
    order = await _get_locked_order(session, order_id)
    if order.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm order with status '{order.status}'. Order must be PENDING.",
        )

    order.status = "CONFIRMED"
    await session.commit()
    session.expire_all()
    reloaded_order = await _get_locked_order(session, order_id)
    return build_fulfillment_order_read(reloaded_order)


async def allocate_order_fefo(session: AsyncSession, order_id: UUID) -> OrderRead:
    """
    Executes server-side FEFO batch allocation for a CONFIRMED order:
    1. Ranks active, non-expired inventory batches according to strict 5-level FEFO rules:
       (expiry_date ASC, mfg_date ASC, created_at ASC, quantity_on_hand DESC, batch.id ASC)
    2. Splits order items across eligible batches.
    3. Does NOT increment quantity_reserved (already reserved at checkout).
    4. If any item is under-allocated, rolls back atomically.
    """
    business_date = get_business_date()
    order = await _get_locked_order(session, order_id)
    if order.status != "CONFIRMED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot allocate order with status '{order.status}'. Order must be CONFIRMED.",
        )

    product_ids = sorted(list(set(item.product_id for item in order.items)))

    # Query and lock active, non-expired inventory rows ordered strictly by FEFO hierarchy
    inv_stmt = (
        select(Inventory)
        .join(Inventory.batch)
        .join(Inventory.product)
        .options(
            joinedload(Inventory.batch),
            joinedload(Inventory.product),
        )
        .where(
            Inventory.product_id.in_(product_ids),
            Product.is_active == True,
            Batch.status == "active",
            Batch.expiry_date >= business_date,
            Inventory.quantity_on_hand > 0,
        )
        .order_by(
            Inventory.product_id.asc(),
            Batch.expiry_date.asc(),
            Batch.manufacturing_date.asc().nulls_last(),
            Batch.created_at.asc(),
            Inventory.quantity_on_hand.desc(),
            Batch.id.asc(),
        )
        .with_for_update()
    )
    inv_res = await session.execute(inv_stmt)
    locked_inventories = inv_res.scalars().unique().all()

    # Group locked inventory records by product_id
    inv_by_product: dict[UUID, list[Inventory]] = {pid: [] for pid in product_ids}
    for inv in locked_inventories:
        inv_by_product[inv.product_id].append(inv)

    # Perform FEFO batch allocation for each OrderItem
    for item in order.items:
        ranked_inv_list = inv_by_product.get(item.product_id, [])
        remaining_needed = item.quantity

        for target_inv in ranked_inv_list:
            if remaining_needed <= 0:
                break

            on_hand = target_inv.quantity_on_hand or 0
            if on_hand <= 0:
                continue

            take_qty = min(remaining_needed, on_hand)
            if take_qty > 0:
                alloc = OrderBatchAllocation(
                    order_item_id=item.id,
                    order_id=order.id,
                    product_id=item.product_id,
                    batch_id=target_inv.batch_id,
                    inventory_id=target_inv.id,
                    allocated_quantity=take_qty,
                )
                session.add(alloc)
                remaining_needed -= take_qty

        if remaining_needed > 0:
            prod_name = item.product.name if item.product else "Product"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock available across valid non-expired FEFO batches for '{prod_name}'. Unallocated: {remaining_needed}.",
            )

        item.fulfillment_status = "ALLOCATED"

    order.status = "ALLOCATED"
    await session.commit()
    session.expire_all()
    reloaded_order = await _get_locked_order(session, order_id)
    return build_fulfillment_order_read(reloaded_order)


async def pack_order(session: AsyncSession, order_id: UUID) -> OrderRead:
    """Transitions order from ALLOCATED -> PACKED."""
    order = await _get_locked_order(session, order_id)
    if order.status != "ALLOCATED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pack order with status '{order.status}'. Order must be ALLOCATED.",
        )

    for item in order.items:
        if item.fulfillment_status != "ALLOCATED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order item '{item.id}' is not fully allocated.",
            )
        item.fulfillment_status = "PACKED"

    order.status = "PACKED"
    await session.commit()
    session.expire_all()
    reloaded = await _get_locked_order(session, order_id)
    return build_fulfillment_order_read(reloaded)


async def dispatch_order(session: AsyncSession, order_id: UUID) -> OrderRead:
    """
    Transitions order from PACKED -> SHIPPED:
    Physically deducts stock from inventory (quantity_on_hand -= qty, quantity_reserved -= qty)
    and logs 'SALE' InventoryTransaction audit logs.
    """
    order = await _get_locked_order(session, order_id)
    if order.status != "PACKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot dispatch order with status '{order.status}'. Order must be PACKED.",
        )

    # Collect allocated inventory IDs
    inv_ids = sorted(list(set(alloc.inventory_id for item in order.items for alloc in item.allocations)))

    inv_stmt = (
        select(Inventory)
        .where(Inventory.id.in_(inv_ids))
        .order_by(Inventory.product_id.asc(), Inventory.id.asc())
        .with_for_update()
    )
    inv_res = await session.execute(inv_stmt)
    inventory_map = {inv.id: inv for inv in inv_res.scalars().unique().all()}

    # Physically deduct stock & record SALE transaction log
    for item in order.items:
        for alloc in item.allocations:
            inv = inventory_map.get(alloc.inventory_id)
            if not inv:
                continue

            deduct_qty = alloc.allocated_quantity
            qty_before = inv.quantity_on_hand

            inv.quantity_on_hand = max(0, (inv.quantity_on_hand or 0) - deduct_qty)
            inv.quantity_reserved = max(0, (inv.quantity_reserved or 0) - deduct_qty)

            tx = InventoryTransaction(
                inventory_id=inv.id,
                transaction_type="SALE",
                quantity_change=-deduct_qty,
                quantity_before=qty_before,
                quantity_after=inv.quantity_on_hand,
                reference_id=order.id,
                reference_type="ORDER",
                notes=f"Physical stock deduction for Order {order.order_number}",
            )
            session.add(tx)

        item.fulfillment_status = "SHIPPED"

    order.status = "SHIPPED"
    await session.commit()
    session.expire_all()
    reloaded = await _get_locked_order(session, order_id)
    return build_fulfillment_order_read(reloaded)


async def deliver_order(session: AsyncSession, order_id: UUID) -> OrderRead:
    """
    Transitions order from SHIPPED -> DELIVERED and synchronously creates consumer PantryItems
    from exact OrderBatchAllocation records within the same database transaction.
    """
    order = await _get_locked_order(session, order_id)
    if order.status != "SHIPPED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot deliver order with status '{order.status}'. Order must be SHIPPED.",
        )

    # Get or create consumer's default home pantry
    pantry_stmt = select(ConsumerPantry).where(
        ConsumerPantry.user_id == order.user_id, ConsumerPantry.is_default == True
    )
    pantry_res = await session.execute(pantry_stmt)
    pantry = pantry_res.scalars().first()
    if not pantry:
        pantry = ConsumerPantry(
            user_id=order.user_id,
            name="My Home Pantry",
            is_default=True,
        )
        session.add(pantry)
        await session.flush()

    for item in order.items:
        item.fulfillment_status = "DELIVERED"
        u_measure = item.product.unit_of_measure if (item.product and item.product.unit_of_measure) else "units"
        for alloc in item.allocations:
            # Idempotency check: verify whether PantryItem already exists for this (pantry_id, order_item_id, batch_id)
            chk_stmt = select(PantryItem).where(
                PantryItem.pantry_id == pantry.id,
                PantryItem.order_item_id == item.id,
                PantryItem.batch_id == alloc.batch_id,
            )
            chk_res = await session.execute(chk_stmt)
            if not chk_res.scalars().first():
                b_expiry = alloc.batch.expiry_date if alloc.batch else None
                pantry_item = PantryItem(
                    pantry_id=pantry.id,
                    product_id=alloc.product_id,
                    batch_id=alloc.batch_id,
                    order_item_id=item.id,
                    quantity=alloc.allocated_quantity,
                    unit=u_measure,
                    purchase_date=get_business_date(),
                    expiry_date=b_expiry,
                    storage_location="pantry",
                    status="active",
                )
                session.add(pantry_item)
                await session.flush()
                session.add(
                    PantryItemLog(
                        pantry_item_id=pantry_item.id,
                        action="SYNCED_FROM_ORDER",
                        quantity_change=alloc.allocated_quantity,
                    )
                )

    order.status = "DELIVERED"
    await session.commit()
    reloaded = await _get_locked_order(session, order_id)
    return build_fulfillment_order_read(reloaded)


async def cancel_order(
    session: AsyncSession, order_id: UUID, user_id: UUID, is_consumer: bool = False
) -> OrderRead:
    """
    Cancels an order pre-shipment (PENDING, CONFIRMED, ALLOCATED, PACKED):
    Releases quantity_reserved on inventory and logs 'RELEASE' InventoryTransactions.
    """
    order = await _get_locked_order(session, order_id)

    if is_consumer and order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found.",
        )

    allowed_cancel_statuses = ("PENDING", "CONFIRMED", "ALLOCATED", "PACKED")
    if order.status not in allowed_cancel_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel order with status '{order.status}'. Order has already been dispatched or completed.",
        )

    # Gather inventory records to release reserved stock
    if order.status in ("ALLOCATED", "PACKED"):
        alloc_inv_ids = [alloc.inventory_id for item in order.items for alloc in item.allocations]
        inv_stmt = (
            select(Inventory)
            .where(Inventory.id.in_(alloc_inv_ids))
            .order_by(Inventory.product_id.asc(), Inventory.id.asc())
            .with_for_update()
        )
        inv_res = await session.execute(inv_stmt)
        inventory_map = {inv.id: inv for inv in inv_res.scalars().unique().all()}

        for item in order.items:
            for alloc in item.allocations:
                inv = inventory_map.get(alloc.inventory_id)
                if inv:
                    qty_before_res = inv.quantity_reserved
                    inv.quantity_reserved = max(0, (inv.quantity_reserved or 0) - alloc.allocated_quantity)

                    tx = InventoryTransaction(
                        inventory_id=inv.id,
                        transaction_type="RELEASE",
                        quantity_change=-alloc.allocated_quantity,
                        quantity_before=qty_before_res,
                        quantity_after=inv.quantity_reserved,
                        reference_id=order.id,
                        reference_type="ORDER",
                        notes=f"Released stock reservation for cancelled Order {order.order_number}",
                    )
                    session.add(tx)
                await session.delete(alloc)

    else:
        # PENDING or CONFIRMED (reservation was placed on product inventory during checkout)
        product_ids = [item.product_id for item in order.items]
        inv_stmt = (
            select(Inventory)
            .where(Inventory.product_id.in_(product_ids))
            .order_by(Inventory.product_id.asc(), Inventory.id.asc())
            .with_for_update()
        )
        inv_res = await session.execute(inv_stmt)
        inventories = inv_res.scalars().unique().all()

        for item in order.items:
            rem_to_release = item.quantity
            for inv in inventories:
                if inv.product_id != item.product_id or rem_to_release <= 0:
                    continue
                if (inv.quantity_reserved or 0) <= 0:
                    continue

                rel_amount = min(rem_to_release, inv.quantity_reserved)
                qty_before_res = inv.quantity_reserved
                inv.quantity_reserved = max(0, inv.quantity_reserved - rel_amount)
                rem_to_release -= rel_amount

                tx = InventoryTransaction(
                    inventory_id=inv.id,
                    transaction_type="RELEASE",
                    quantity_change=-rel_amount,
                    quantity_before=qty_before_res,
                    quantity_after=inv.quantity_reserved,
                    reference_id=order.id,
                    reference_type="ORDER",
                    notes=f"Released stock reservation for cancelled Order {order.order_number}",
                )
                session.add(tx)

    order.status = "CANCELLED"
    await session.commit()
    session.expire_all()
    reloaded = await _get_locked_order(session, order_id)
    return build_fulfillment_order_read(reloaded)


async def get_order_allocations(
    session: AsyncSession, order_id: UUID, user_id: Optional[UUID] = None, is_consumer: bool = False
) -> List[OrderBatchAllocationRead]:
    """Retrieves batch allocation details for an order."""
    stmt = (
        select(OrderBatchAllocation)
        .options(joinedload(OrderBatchAllocation.batch))
        .join(OrderBatchAllocation.order)
        .where(OrderBatchAllocation.order_id == order_id)
    )

    if is_consumer and user_id:
        stmt = stmt.where(Order.user_id == user_id)

    res = await session.execute(stmt)
    allocs = res.scalars().all()

    if not allocs and is_consumer:
        # Check order existence
        chk = await session.execute(select(Order).where(Order.id == order_id, Order.user_id == user_id))
        if not chk.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID '{order_id}' not found.",
            )

    return [
        OrderBatchAllocationRead(
            id=a.id,
            order_item_id=a.order_item_id,
            order_id=a.order_id,
            product_id=a.product_id,
            batch_id=a.batch_id,
            inventory_id=a.inventory_id,
            allocated_quantity=a.allocated_quantity,
            batch_number=a.batch.batch_number if a.batch else None,
            expiry_date=a.batch.expiry_date if a.batch else None,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in allocs
    ]


async def list_all_orders(session: AsyncSession, status_filter: Optional[str] = None) -> List[OrderRead]:
    """Lists operational orders for business roles with optional status filter."""
    stmt = (
        select(Order)
        .options(
            joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.category),
            joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.brand),
            joinedload(Order.items).joinedload(OrderItem.allocations).joinedload(OrderBatchAllocation.batch),
        )
        .where(Order.is_deleted == False)
    )

    if status_filter:
        stmt = stmt.where(Order.status == status_filter.upper())

    stmt = stmt.order_by(Order.created_at.desc())
    res = await session.execute(stmt)
    orders = res.scalars().unique().all()
    return [build_fulfillment_order_read(order) for order in orders]


async def get_business_order_by_id(session: AsyncSession, order_id: UUID) -> OrderRead:
    """Gets business order detail view by ID."""
    order = await _get_locked_order(session, order_id)
    return build_fulfillment_order_read(order)
