"""
AVENZO Backend — Consumer Checkout Service
Handles atomic checkout execution, price snapshotting, pessimistic inventory row locking,
stock reservation, idempotency deduplication, and order generation.
"""

import random
import string
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.core.date_utils import get_business_date, get_utc_now
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from app.models.order_allocation import OrderBatchAllocation
from app.models.product import Product
from app.models.inventory import Inventory, Batch, InventoryTransaction
from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.schemas.order import OrderCheckoutRequest, OrderRead, OrderItemRead
from app.schemas.order_allocation import OrderBatchAllocationRead
from app.schemas.marketplace import MarketplaceProductRead
from app.services import marketplace_service


def generate_order_number() -> str:
    """Generates unique order number in format AVZ-YYYYMMDD-XXXX."""
    date_str = get_utc_now().strftime("%Y%m%d")
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"AVZ-{date_str}-{random_str}"


async def get_order_by_id(session: AsyncSession, order_id: UUID, user_id: UUID) -> OrderRead:
    """Retrieves order details for consumer."""
    stmt = (
        select(Order)
        .options(
            joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.category),
            joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.brand),
            joinedload(Order.items).joinedload(OrderItem.allocations).joinedload(OrderBatchAllocation.batch),
        )
        .where(Order.id == order_id, Order.user_id == user_id, Order.is_deleted == False)
    )
    result = await session.execute(stmt)
    order = result.scalars().unique().first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found.",
        )

    return build_order_read_model(order)


async def list_user_orders(session: AsyncSession, user_id: UUID) -> List[OrderRead]:
    """Lists order history for specified consumer."""
    stmt = (
        select(Order)
        .options(
            joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.category),
            joinedload(Order.items).joinedload(OrderItem.product).joinedload(Product.brand),
            joinedload(Order.items).joinedload(OrderItem.allocations).joinedload(OrderBatchAllocation.batch),
        )
        .where(Order.user_id == user_id, Order.is_deleted == False)
        .order_by(Order.created_at.desc())
    )
    result = await session.execute(stmt)
    orders = result.scalars().unique().all()
    return [build_order_read_model(o) for o in orders]


def build_order_read_model(order: Order) -> OrderRead:
    """Helper to convert Order ORM into OrderRead Pydantic response."""
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


async def process_checkout(
    session: AsyncSession,
    user_id: UUID,
    data: OrderCheckoutRequest,
    idempotency_key: Optional[str] = None,
) -> OrderRead:
    """
    Executes atomic checkout transaction:
    1. Deduplicates via Idempotency-Key if provided.
    2. Validates active cart and line items (and publication status if demo purchase).
    3. Acquires SELECT FOR UPDATE pessimistic locks on Inventory in product_id ASC order.
    4. Re-validates stock availability under row locks with FEFO ordering.
    5. Calculates authoritative pricing, subtotal, and delivery fee.
    6. Creates Order & OrderItems with unit_price snapshots.
    7. For demo purchases:
       - Directly allocates stock via FEFO (OrderBatchAllocation)
       - Deducts physical warehouse stock (quantity_on_hand -= qty) with SALE transactions
       - Synchronously creates separate PantryItems for each allocation with batch expiry date
       - Marks Order DELIVERED and payment PAID
       - Converts cart atomically in one transaction
    8. For standard orders:
       - Reserves stock (quantity_reserved += quantity) & logs RESERVATION transactions
       - Leaves status PENDING for warehouse fulfillment
       - Converts cart
    """
    # 1. Idempotency Check
    if idempotency_key:
        stmt_idem = select(Order).where(Order.user_id == user_id, Order.idempotency_key == idempotency_key)
        res_idem = await session.execute(stmt_idem)
        existing_order = res_idem.scalars().first()
        if existing_order:
            return await get_order_by_id(session, existing_order.id, user_id)

    # 2. Fetch Active Cart
    cart_stmt = (
        select(Cart)
        .options(
            joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.category),
        )
        .where(Cart.user_id == user_id, Cart.status == "ACTIVE")
    )
    cart_res = await session.execute(cart_stmt)
    cart = cart_res.scalars().unique().first()

    if not cart or not cart.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot checkout: Active shopping cart is empty.",
        )

    # Filter valid items
    valid_items = [item for item in cart.items if item.product and item.product.is_active and not item.product.is_deleted]
    if not valid_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot checkout: Cart contains no active products.",
        )

    # Re-validate publication and category active status for demo purchases
    if data.demo_purchase:
        for item in cart.items:
            prod = item.product
            if not prod or not prod.is_active or prod.is_deleted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{prod.name if prod else 'Item'}' is inactive or deleted.",
                )
            if not getattr(prod, "is_published", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{prod.name}' is a draft and cannot be purchased in marketplace.",
                )
            if prod.category and not prod.category.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category for product '{prod.name}' is inactive.",
                )

    product_ids = sorted(list(set(item.product_id for item in valid_items)))

    # 3. Lock Inventory Rows in Deterministic Order (product_id ASC, inventory.id ASC)
    lock_stmt = (
        select(Inventory)
        .options(joinedload(Inventory.batch), joinedload(Inventory.product))
        .where(Inventory.product_id.in_(product_ids))
        .order_by(Inventory.product_id.asc(), Inventory.id.asc())
        .with_for_update()
    )
    lock_res = await session.execute(lock_stmt)
    locked_inventories = lock_res.scalars().unique().all()

    # 4. Check Stock Availability Under Row Lock
    ref_date = get_business_date()
    avail_map: dict[UUID, list[Inventory]] = {pid: [] for pid in product_ids}
    total_avail_qty: dict[UUID, int] = {pid: 0 for pid in product_ids}

    for inv in locked_inventories:
        batch = inv.batch
        if not batch or batch.status != "active":
            continue
        if inv.product and inv.product.has_expiry and batch.expiry_date and batch.expiry_date < ref_date:
            continue

        net_avail = max(0, (inv.quantity_on_hand or 0) - (inv.quantity_reserved or 0))
        if net_avail > 0:
            avail_map[inv.product_id].append(inv)
            total_avail_qty[inv.product_id] += net_avail

    # Rank inventories per product using strict FEFO
    for pid in product_ids:
        avail_map[pid].sort(
            key=lambda inv: (
                inv.batch.expiry_date if (inv.batch and inv.batch.expiry_date) else date.max,
                inv.batch.manufacturing_date if (inv.batch and inv.batch.manufacturing_date) else date.max,
                inv.batch.created_at if (inv.batch and inv.batch.created_at) else datetime.max,
                -max(0, (inv.quantity_on_hand or 0) - (inv.quantity_reserved or 0)),
                str(inv.batch.id) if inv.batch else str(inv.id),
            )
        )

    # Validate stock sufficiency for every item
    for item in valid_items:
        avail_qty = total_avail_qty.get(item.product_id, 0)
        if item.quantity > avail_qty:
            prod_name = item.product.name if item.product else "Product"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock available for '{prod_name}'. Requested: {item.quantity}, Available: {avail_qty}.",
            )

    # 5. Authoritative Pricing & Order Creation
    subtotal = Decimal("0.00")
    order_items_data: list[Tuple[Product, int, Decimal, Decimal]] = []

    for item in valid_items:
        prod = item.product
        unit_price = prod.unit_price or Decimal("0.00")
        line_total = Decimal(item.quantity) * unit_price
        subtotal += line_total
        order_items_data.append((prod, item.quantity, unit_price, line_total))

    if data.demo_purchase:
        delivery_fee = Decimal("0.00")
        order_status = "DELIVERED"
        payment_status = "DEMO_COMPLETED"
    else:
        # Standard deterministic delivery fee: $5.00, or FREE ($0.00) for orders >= $50.00
        delivery_fee = Decimal("0.00") if subtotal >= Decimal("50.00") else Decimal("5.00")
        order_status = "PENDING"
        payment_status = "PAID" if data.payment_method == "MOCK_PAYMENT" else "UNPAID"

    total_amount = subtotal + delivery_fee
    order_number = generate_order_number()

    order = Order(
        order_number=order_number,
        user_id=user_id,
        status=order_status,
        payment_status=payment_status,
        payment_method=data.payment_method,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total_amount=total_amount,
        shipping_address=data.shipping_address,
        notes=data.notes,
        idempotency_key=idempotency_key,
    )
    session.add(order)
    await session.flush()

    if data.demo_purchase:
        # Get or create default home pantry for the consumer
        pantry_stmt = select(ConsumerPantry).where(
            ConsumerPantry.user_id == user_id, ConsumerPantry.is_default == True
        )
        pantry_res = await session.execute(pantry_stmt)
        pantry = pantry_res.scalars().first()
        if not pantry:
            pantry = ConsumerPantry(
                user_id=user_id,
                name="My Home Pantry",
                is_default=True,
            )
            session.add(pantry)
            await session.flush()

        # Atomic FEFO allocation, stock deduction, and PantryItem creation
        for prod, qty, price, line_tot in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                quantity=qty,
                unit_price=price,
                total_price=line_tot,
                fulfillment_status="DELIVERED",
            )
            session.add(order_item)
            await session.flush()

            rem_to_allocate = qty
            inv_list = avail_map.get(prod.id, [])

            for inv in inv_list:
                if rem_to_allocate <= 0:
                    break
                avail = max(0, (inv.quantity_on_hand or 0) - (inv.quantity_reserved or 0))
                if avail <= 0:
                    continue

                take_qty = min(rem_to_allocate, avail)
                alloc = OrderBatchAllocation(
                    order_item_id=order_item.id,
                    order_id=order.id,
                    product_id=prod.id,
                    batch_id=inv.batch_id,
                    inventory_id=inv.id,
                    allocated_quantity=take_qty,
                )
                session.add(alloc)

                # Physical stock deduction
                qty_before = inv.quantity_on_hand
                inv.quantity_on_hand = max(0, (inv.quantity_on_hand or 0) - take_qty)
                rem_to_allocate -= take_qty

                # Audit transaction
                tx = InventoryTransaction(
                    inventory_id=inv.id,
                    transaction_type="SALE",
                    quantity_change=-take_qty,
                    quantity_before=qty_before,
                    quantity_after=inv.quantity_on_hand,
                    reference_id=order.id,
                    reference_type="ORDER",
                    notes=f"Demo purchase stock deduction of {take_qty} units for Order {order_number}",
                )
                session.add(tx)

                # Create separate Pantry item for each distinct batch allocation
                batch_expiry = inv.batch.expiry_date if (prod.has_expiry and inv.batch) else None
                u_measure = prod.unit_of_measure or "units"

                pantry_item = PantryItem(
                    pantry_id=pantry.id,
                    product_id=prod.id,
                    batch_id=inv.batch_id,
                    order_item_id=order_item.id,
                    quantity=take_qty,
                    unit=u_measure,
                    purchase_date=get_business_date(),
                    expiry_date=batch_expiry,
                    storage_location="pantry",
                    status="active",
                )
                session.add(pantry_item)
                await session.flush()

                session.add(
                    PantryItemLog(
                        pantry_item_id=pantry_item.id,
                        action="SYNCED_FROM_ORDER",
                        quantity_change=take_qty,
                    )
                )

        # Mark Cart CONVERTED
        cart.status = "CONVERTED"
        await session.commit()
        return await get_order_by_id(session, order.id, user_id)
    else:
        # Standard warehouse multi-stage fulfillment flow
        for prod, qty, price, line_tot in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=prod.id,
                quantity=qty,
                unit_price=price,
                total_price=line_tot,
                fulfillment_status="UNALLOCATED",
            )
            session.add(order_item)

        # 6. Inventory Reservation Stock Increment
        for prod, qty, price, line_tot in order_items_data:
            rem_to_reserve = qty
            inv_list = avail_map.get(prod.id, [])

            for inv in inv_list:
                if rem_to_reserve <= 0:
                    break
                net_avail = max(0, (inv.quantity_on_hand or 0) - (inv.quantity_reserved or 0))
                if net_avail <= 0:
                    continue

                reserve_amount = min(rem_to_reserve, net_avail)
                qty_before_res = inv.quantity_reserved
                inv.quantity_reserved = qty_before_res + reserve_amount
                rem_to_reserve -= reserve_amount

                # Audit transaction log
                tx = InventoryTransaction(
                    inventory_id=inv.id,
                    transaction_type="RESERVATION",
                    quantity_change=reserve_amount,
                    quantity_before=qty_before_res,
                    quantity_after=inv.quantity_reserved,
                    reference_id=order.id,
                    reference_type="ORDER",
                    notes=f"Stock reservation of {reserve_amount} units for Order {order_number}",
                )
                session.add(tx)

        # 7. Convert Cart
        cart.status = "CONVERTED"
        await session.commit()

        return await get_order_by_id(session, order.id, user_id)

