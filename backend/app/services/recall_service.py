"""
AVENZO Backend — Batch Recall Intelligence Service
Traceability query engine, PantryItem recall marking, and deterministic notification fanout.
"""

from uuid import UUID
from typing import List, Set, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.core.database import get_db
from app.models.inventory import Batch
from app.models.order import Order, OrderItem
from app.models.order_allocation import OrderBatchAllocation
from app.models.pantry import PantryItem, PantryItemLog
from app.models.notification import NotificationRecord
from app.models.base import utc_now
from app.schemas.recall import BatchRecallRequest, BatchRecallImpactResponse
from app.services import notification_service


async def calculate_recall_impact(session: AsyncSession, batch_id: UUID) -> BatchRecallImpactResponse:
    """
    Previews or calculates the batch recall impact:
    Counts delivered orders, affected consumers, and linked pantry items for exact recalled batch.
    """
    stmt = (
        select(Batch)
        .options(joinedload(Batch.product))
        .where(Batch.id == batch_id)
    )
    res = await session.execute(stmt)
    batch = res.scalars().first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with ID '{batch_id}' not found.",
        )

    # Fetch delivered allocations for exact batch
    alloc_stmt = (
        select(
            OrderBatchAllocation.order_id,
            Order.user_id,
            OrderBatchAllocation.order_item_id,
        )
        .join(Order, Order.id == OrderBatchAllocation.order_id)
        .where(
            OrderBatchAllocation.batch_id == batch_id,
            Order.status == "DELIVERED",
            Order.is_deleted == False,
        )
    )
    alloc_res = await session.execute(alloc_stmt)
    alloc_rows = alloc_res.all()

    affected_orders: Set[UUID] = set()
    affected_users: Set[UUID] = set()
    affected_order_items: Set[UUID] = set()

    for row in alloc_rows:
        affected_orders.add(row.order_id)
        affected_users.add(row.user_id)
        affected_order_items.add(row.order_item_id)

    # Query affected pantry items
    pantry_count = 0
    if affected_order_items:
        pantry_stmt = select(func.count(PantryItem.id)).where(
            PantryItem.batch_id == batch_id,
            PantryItem.order_item_id.in_(list(affected_order_items)),
            PantryItem.is_deleted == False,
        )
        pantry_res = await session.execute(pantry_stmt)
        pantry_count = pantry_res.scalar() or 0

    return BatchRecallImpactResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        product_id=batch.product_id,
        product_name=batch.product.name if batch.product else "Product",
        is_already_recalled=(batch.status == "recalled"),
        affected_orders_count=len(affected_orders),
        affected_consumers_count=len(affected_users),
        affected_pantry_items_count=pantry_count,
        notifications_sent_count=0,
        recalled_at=batch.recalled_at,
        recall_reason=batch.recall_reason,
    )


async def recall_batch(
    session: AsyncSession, batch_id: UUID, user_id: UUID, data: BatchRecallRequest
) -> BatchRecallImpactResponse:
    """
    Executes a Batch Recall operation with row-locking and idempotency:
    1. Locks Batch row with FOR UPDATE.
    2. If already recalled, returns current impact summary without duplicating notifications.
    3. Updates Batch status = 'recalled' and records recall metadata.
    4. Identifies delivered orders and consumers linked to exact batch.
    5. Marks associated PantryItems with is_recalled = True.
    6. Dispatches deterministic BATCH_RECALL notifications to affected consumers.
    """
    # 1. Lock Batch row
    batch_stmt = (
        select(Batch)
        .options(joinedload(Batch.product))
        .where(Batch.id == batch_id)
        .with_for_update()
    )
    batch_res = await session.execute(batch_stmt)
    batch = batch_res.scalars().first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with ID '{batch_id}' not found.",
        )

    # 2. Idempotent check
    if batch.status == "recalled":
        impact = await calculate_recall_impact(session, batch_id)
        impact.is_already_recalled = True
        return impact

    now = utc_now()
    batch.status = "recalled"
    batch.recalled_at = now
    batch.recall_reason = data.recall_reason
    batch.recalled_by = user_id

    # 3. Find delivered allocations
    alloc_stmt = (
        select(
            OrderBatchAllocation.order_id,
            Order.user_id,
            Order.order_number,
            OrderBatchAllocation.order_item_id,
        )
        .join(Order, Order.id == OrderBatchAllocation.order_id)
        .where(
            OrderBatchAllocation.batch_id == batch_id,
            Order.status == "DELIVERED",
            Order.is_deleted == False,
        )
    )
    alloc_res = await session.execute(alloc_stmt)
    alloc_rows = alloc_res.all()

    affected_orders: Set[UUID] = set()
    affected_users: Set[UUID] = set()
    affected_order_items: Set[UUID] = set()
    user_order_map: Dict[UUID, str] = {}

    for row in alloc_rows:
        affected_orders.add(row.order_id)
        affected_users.add(row.user_id)
        affected_order_items.add(row.order_item_id)
        user_order_map[row.user_id] = row.order_number

    # 4. Mark affected PantryItems as recalled
    pantry_count = 0
    if affected_order_items:
        pantry_stmt = (
            select(PantryItem)
            .where(
                PantryItem.batch_id == batch_id,
                PantryItem.order_item_id.in_(list(affected_order_items)),
                PantryItem.is_deleted == False,
            )
            .with_for_update()
        )
        pantry_res = await session.execute(pantry_stmt)
        pantry_items = pantry_res.scalars().all()
        pantry_count = len(pantry_items)

        for p_item in pantry_items:
            p_item.is_recalled = True
            p_item.recalled_at = now
            p_item.recall_reason = data.recall_reason
            session.add(
                PantryItemLog(
                    pantry_item_id=p_item.id,
                    action="RECALLED",
                    quantity_change=0,
                )
            )

    # 5. Deterministic Notification Fanout
    notifications_sent = 0
    product_name = batch.product.name if batch.product else "Product"

    for consumer_user_id in affected_users:
        # Check deduplication index
        dedup_stmt = select(NotificationRecord).where(
            NotificationRecord.user_id == consumer_user_id,
            NotificationRecord.notification_type == "BATCH_RECALL",
            NotificationRecord.reference_type == "BATCH",
            NotificationRecord.reference_id == batch_id,
        )
        dedup_res = await session.execute(dedup_stmt)
        if not dedup_res.scalars().first():
            ord_num = user_order_map.get(consumer_user_id, "")
            title = f"URGENT: Safety Recall for {product_name}"
            body = (
                f"Batch {batch.batch_number} of '{product_name}' delivered in order {ord_num} "
                f"has been recalled. Reason: {data.recall_reason}. Please do NOT consume."
            )
            # Create notification record with reference fields
            rec = NotificationRecord(
                user_id=consumer_user_id,
                notification_type="BATCH_RECALL",
                title=title,
                body=body,
                reference_type="BATCH",
                reference_id=batch_id,
                status="CREATED",
                is_read=False,
            )
            session.add(rec)
            notifications_sent += 1

    await session.commit()

    return BatchRecallImpactResponse(
        batch_id=batch.id,
        batch_number=batch.batch_number,
        product_id=batch.product_id,
        product_name=product_name,
        is_already_recalled=False,
        affected_orders_count=len(affected_orders),
        affected_consumers_count=len(affected_users),
        affected_pantry_items_count=pantry_count,
        notifications_sent_count=notifications_sent,
        recalled_at=now,
        recall_reason=data.recall_reason,
    )
