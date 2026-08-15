"""
AVENZO Backend — Inventory Service
Business logic for managing stock balances and recording Inventory Transactions.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.models.inventory import Inventory, InventoryTransaction, Batch
from app.models.product import Product
from app.models.warehouse import Warehouse, WarehouseLocation
from app.schemas.inventory import InventoryAdjustRequest


async def get_inventory_by_id(session: AsyncSession, inventory_id: UUID) -> Inventory:
    """Get inventory record by ID with eager nested relationships."""
    result = await session.execute(
        select(Inventory)
        .options(
            joinedload(Inventory.product).joinedload(Product.category),
            joinedload(Inventory.product).joinedload(Product.brand),
            joinedload(Inventory.batch).joinedload(Batch.supplier),
            joinedload(Inventory.warehouse).joinedload(Warehouse.locations),
            joinedload(Inventory.location),
        )
        .where(Inventory.id == inventory_id)
    )
    inv = result.scalars().unique().first()
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory record with id '{inventory_id}' not found.",
        )
    return inv


async def list_inventory(
    session: AsyncSession,
    warehouse_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    batch_id: Optional[UUID] = None,
) -> List[Inventory]:
    """List inventory balances with optional filters."""
    stmt = select(Inventory).options(
        joinedload(Inventory.product).joinedload(Product.category),
        joinedload(Inventory.product).joinedload(Product.brand),
        joinedload(Inventory.batch).joinedload(Batch.supplier),
        joinedload(Inventory.warehouse).joinedload(Warehouse.locations),
        joinedload(Inventory.location),
    )

    if warehouse_id:
        stmt = stmt.where(Inventory.warehouse_id == warehouse_id)
    if product_id:
        stmt = stmt.where(Inventory.product_id == product_id)
    if batch_id:
        stmt = stmt.where(Inventory.batch_id == batch_id)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def adjust_inventory(
    session: AsyncSession, request: InventoryAdjustRequest, performed_by_id: Optional[UUID] = None
) -> Inventory:
    """
    Adjusts inventory stock level and records an InventoryTransaction audit log.
    Creates new Inventory record if no record exists for (batch, warehouse, location).
    """
    # Verify product, batch, warehouse exist
    prod = await session.execute(select(Product).where(Product.id == request.product_id, Product.is_deleted == False))
    if not prod.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{request.product_id}' not found.")

    batch = await session.execute(select(Batch).where(Batch.id == request.batch_id))
    if not batch.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Batch '{request.batch_id}' not found.")

    wh = await session.execute(select(Warehouse).where(Warehouse.id == request.warehouse_id))
    if not wh.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Warehouse '{request.warehouse_id}' not found.")

    if request.location_id:
        loc = await session.execute(select(WarehouseLocation).where(WarehouseLocation.id == request.location_id))
        if not loc.scalars().first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Location '{request.location_id}' not found.")

    # Find existing inventory balance
    inv_res = await session.execute(
        select(Inventory).where(
            Inventory.batch_id == request.batch_id,
            Inventory.warehouse_id == request.warehouse_id,
            Inventory.location_id == request.location_id,
        )
    )
    inv = inv_res.scalars().first()

    if not inv:
        if request.quantity_change < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deduct stock: No existing inventory record found.",
            )
        inv = Inventory(
            product_id=request.product_id,
            batch_id=request.batch_id,
            warehouse_id=request.warehouse_id,
            location_id=request.location_id,
            quantity_on_hand=0,
            quantity_reserved=0,
        )
        session.add(inv)
        await session.flush()

    qty_before = inv.quantity_on_hand
    qty_after = qty_before + request.quantity_change

    if qty_after < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock on hand ({qty_before}) for reduction of {abs(request.quantity_change)}.",
        )

    inv.quantity_on_hand = qty_after

    # Create transaction log
    transaction = InventoryTransaction(
        inventory_id=inv.id,
        transaction_type=request.transaction_type,
        quantity_change=request.quantity_change,
        quantity_before=qty_before,
        quantity_after=qty_after,
        notes=request.notes,
        performed_by=performed_by_id,
    )
    session.add(transaction)

    await session.commit()
    return await get_inventory_by_id(session, inv.id)


async def list_transactions(
    session: AsyncSession, inventory_id: Optional[UUID] = None, skip: int = 0, limit: int = 50
) -> List[InventoryTransaction]:
    """List inventory audit transactions."""
    stmt = select(InventoryTransaction).order_by(InventoryTransaction.created_at.desc())
    if inventory_id:
        stmt = stmt.where(InventoryTransaction.inventory_id == inventory_id)
    stmt = stmt.offset(skip).limit(limit)

    result = await session.execute(stmt)
    return result.scalars().all()
