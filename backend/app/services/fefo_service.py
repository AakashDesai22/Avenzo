"""
AVENZO Backend — FEFO (First-Expired, First-Out) Engine Service
Business logic for FEFO batch ranking, read-only allocation previews,
and non-blocking FEFO violation detection with audit logging.
"""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.core.date_utils import get_business_date
from app.models.inventory import Inventory, Batch, InventoryTransaction
from app.models.product import Product
from app.models.warehouse import Warehouse, WarehouseLocation
from app.services.expiry_service import calculate_dte, classify_expiry_status
from app.schemas.fefo import (
    FEFORankedBatchRead,
    FEFOBatchAllocationItem,
    FEFOAllocationPlanResponse,
    FEFOVerificationResponse,
)


async def get_fefo_ranked_batches(
    session: AsyncSession, product_id: UUID, warehouse_id: Optional[UUID] = None
) -> List[FEFORankedBatchRead]:
    """
    Retrieves and ranks eligible inventory batches for a product according to strict FEFO rules:
    1. batch.expiry_date ASC
    2. batch.manufacturing_date ASC
    3. batch.created_at ASC
    4. inventory.quantity_available DESC
    5. batch.id ASC
    Filters out inactive products, non-expiry products, expired/recalled batches, and zero-available stock.
    """
    business_date = get_business_date()

    # Verify product exists and has expiry enabled
    prod_res = await session.execute(
        select(Product).where(Product.id == product_id, Product.is_deleted == False)
    )
    product = prod_res.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )

    if not product.has_expiry:
        # Non-expiry product -> FEFO is not applicable
        return []

    stmt = (
        select(Inventory)
        .join(Inventory.batch)
        .join(Inventory.product)
        .join(Inventory.warehouse)
        .options(
            joinedload(Inventory.product).joinedload(Product.category),
            joinedload(Inventory.product).joinedload(Product.brand),
            joinedload(Inventory.batch).joinedload(Batch.supplier),
            joinedload(Inventory.warehouse).joinedload(Warehouse.locations),
            joinedload(Inventory.location),
        )
        .where(
            Inventory.product_id == product_id,
            Product.is_active == True,
            Batch.status == "active",
            Batch.expiry_date >= business_date,
            (Inventory.quantity_on_hand - Inventory.quantity_reserved) > 0,
        )
    )

    if warehouse_id:
        stmt = stmt.where(Inventory.warehouse_id == warehouse_id)

    # Apply 5-level FEFO ranking
    stmt = stmt.order_by(
        Batch.expiry_date.asc(),
        Batch.manufacturing_date.asc().nulls_last(),
        Batch.created_at.asc(),
        (Inventory.quantity_on_hand - Inventory.quantity_reserved).desc(),
        Batch.id.asc(),
    )

    result = await session.execute(stmt)
    inventories = result.scalars().unique().all()

    ranked_items: List[FEFORankedBatchRead] = []
    for rank, inv in enumerate(inventories, start=1):
        dte = calculate_dte(inv.batch.expiry_date, target_date=business_date)
        exp_status = classify_expiry_status(inv.batch.expiry_date, has_expiry=True, target_date=business_date)

        ranked_items.append(
            FEFORankedBatchRead(
                batch_id=inv.batch_id,
                batch_number=inv.batch.batch_number,
                product_id=inv.product_id,
                product_name=inv.product.name,
                sku=inv.product.sku,
                has_expiry=inv.product.has_expiry,
                manufacturing_date=inv.batch.manufacturing_date,
                expiry_date=inv.batch.expiry_date,
                days_to_expiry=dte,
                expiry_status=exp_status,
                quantity_on_hand=inv.quantity_on_hand,
                quantity_reserved=inv.quantity_reserved,
                quantity_available=inv.quantity_available,
                warehouse_id=inv.warehouse_id,
                warehouse_name=inv.warehouse.name,
                location_id=inv.location_id,
                location_code=inv.location.location_code if inv.location else None,
                fefo_rank=rank,
            )
        )

    return ranked_items


async def generate_allocation_preview(
    session: AsyncSession, product_id: UUID, requested_quantity: int, warehouse_id: Optional[UUID] = None
) -> FEFOAllocationPlanResponse:
    """
    READ-ONLY FEFO Allocation Preview.
    Calculates stock pick allocations strictly according to FEFO rules.
    MUST NOT mutate inventory balances or database state.
    """
    prod_res = await session.execute(
        select(Product).where(Product.id == product_id, Product.is_deleted == False)
    )
    product = prod_res.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )

    ranked_batches = await get_fefo_ranked_batches(session, product_id, warehouse_id)

    allocations: List[FEFOBatchAllocationItem] = []
    remaining_needed = requested_quantity
    allocated_total = 0

    for batch_item in ranked_batches:
        if remaining_needed <= 0:
            break

        take_qty = min(remaining_needed, batch_item.quantity_available)
        if take_qty > 0:
            allocations.append(
                FEFOBatchAllocationItem(
                    batch_id=batch_item.batch_id,
                    batch_number=batch_item.batch_number,
                    manufacturing_date=batch_item.manufacturing_date,
                    expiry_date=batch_item.expiry_date,
                    days_to_expiry=batch_item.days_to_expiry,
                    expiry_status=batch_item.expiry_status,
                    allocated_quantity=take_qty,
                    quantity_available=batch_item.quantity_available,
                    warehouse_id=batch_item.warehouse_id,
                    warehouse_name=batch_item.warehouse_name,
                    location_id=batch_item.location_id,
                    location_code=batch_item.location_code,
                    fefo_rank=batch_item.fefo_rank,
                )
            )
            allocated_total += take_qty
            remaining_needed -= take_qty

    return FEFOAllocationPlanResponse(
        product_id=product_id,
        product_name=product.name,
        sku=product.sku,
        requested_quantity=requested_quantity,
        allocated_total=allocated_total,
        remaining_unallocated=remaining_needed,
        is_fully_allocated=(remaining_needed == 0),
        allocations=allocations,
    )


async def verify_selection_and_audit(
    session: AsyncSession,
    product_id: UUID,
    selected_batch_id: UUID,
    requested_quantity: int,
    warehouse_id: Optional[UUID] = None,
    override_reason: Optional[str] = None,
    performed_by_id: Optional[UUID] = None,
) -> FEFOVerificationResponse:
    """
    Evaluates whether selecting selected_batch_id violates FEFO rules by skipping available earlier-expiring stock.
    If an earlier-expiring batch had available stock that was bypassed, returns a warning and logs a FEFO_VIOLATION audit transaction.
    Non-blocking decision-support behavior.
    """
    ranked_batches = await get_fefo_ranked_batches(session, product_id, warehouse_id)

    if not ranked_batches:
        # No eligible FEFO batches found (e.g. non-expiry product or zero stock)
        return FEFOVerificationResponse(
            is_compliant=True,
            violation_detected=False,
            selected_batch_id=selected_batch_id,
        )

    # Find the selected batch in ranked_batches
    selected_item = next((b for b in ranked_batches if b.batch_id == selected_batch_id), None)
    if not selected_item:
        # Get selected batch directly if it was not in ranked_batches (e.g. inactive or non-FEFO)
        b_res = await session.execute(select(Batch).where(Batch.id == selected_batch_id))
        sel_batch = b_res.scalars().first()
        selected_expiry = sel_batch.expiry_date if sel_batch else None
    else:
        selected_expiry = selected_item.expiry_date

    # Check if there are earlier expiring batches with available stock before selected_batch_id
    earlier_bypassed_batches = []
    bypassed_qty = 0

    for b in ranked_batches:
        if b.batch_id == selected_batch_id:
            break
        # If this earlier batch has expiry earlier than selected batch (or selected batch has no rank)
        if selected_expiry is None or (b.expiry_date and b.expiry_date < selected_expiry):
            earlier_bypassed_batches.append(b)
            bypassed_qty += b.quantity_available

    if earlier_bypassed_batches and bypassed_qty > 0:
        optimal_earlier = earlier_bypassed_batches[0]
        warning_msg = (
            f"FEFO Warning: Selection of batch '{selected_item.batch_number if selected_item else selected_batch_id}' "
            f"(Expires: {selected_expiry}) bypasses {bypassed_qty} available units from earlier-expiring batch "
            f"'{optimal_earlier.batch_number}' (Expires: {optimal_earlier.expiry_date})."
        )

        # Audit log creation in InventoryTransaction
        # Find inventory ID for selected batch if exists
        inv_res = await session.execute(
            select(Inventory).where(Inventory.batch_id == selected_batch_id)
        )
        inv = inv_res.scalars().first()

        if inv:
            tx = InventoryTransaction(
                inventory_id=inv.id,
                transaction_type="FEFO_VIOLATION",
                quantity_change=0,
                quantity_before=inv.quantity_on_hand,
                quantity_after=inv.quantity_on_hand,
                notes=f"{warning_msg} Reason: {override_reason or 'No reason provided'}",
                performed_by=performed_by_id,
            )
            session.add(tx)
            await session.commit()

        return FEFOVerificationResponse(
            is_compliant=False,
            violation_detected=True,
            warning_message=warning_msg,
            selected_batch_id=selected_batch_id,
            selected_expiry_date=selected_expiry,
            earlier_available_batch_id=optimal_earlier.batch_id,
            earlier_available_expiry_date=optimal_earlier.expiry_date,
            bypassed_earlier_quantity=bypassed_qty,
            audit_logged=True if inv else False,
        )

    return FEFOVerificationResponse(
        is_compliant=True,
        violation_detected=False,
        selected_batch_id=selected_batch_id,
        selected_expiry_date=selected_expiry,
        bypassed_earlier_quantity=0,
        audit_logged=False,
    )
