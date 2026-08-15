"""
AVENZO Backend — Batch Service
Business logic for managing Product Batches and Expiry metadata.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.models.inventory import Batch
from app.models.product import Product
from app.schemas.batch import BatchCreate, BatchUpdate


async def create_batch(session: AsyncSession, data: BatchCreate, created_by_id: Optional[UUID] = None) -> Batch:
    """Create a new product batch."""
    # Verify product exists
    prod_res = await session.execute(select(Product).where(Product.id == data.product_id, Product.is_deleted == False))
    if not prod_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{data.product_id}' not found.",
        )

    # Check date constraint
    if data.manufacturing_date and data.expiry_date:
        if data.expiry_date < data.manufacturing_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expiry date cannot precede manufacturing date.",
            )

    # Check duplicate batch_number for this product
    batch_res = await session.execute(
        select(Batch).where(Batch.product_id == data.product_id, Batch.batch_number == data.batch_number)
    )
    if batch_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Batch '{data.batch_number}' already exists for this product.",
        )

    batch = Batch(
        product_id=data.product_id,
        batch_number=data.batch_number,
        manufacturing_date=data.manufacturing_date,
        expiry_date=data.expiry_date,
        supplier_id=data.supplier_id,
        initial_quantity=data.initial_quantity,
        status=data.status,
        notes=data.notes,
        created_by=created_by_id,
    )
    session.add(batch)
    await session.commit()
    return await get_batch_by_id(session, batch.id)


async def get_batch_by_id(session: AsyncSession, batch_id: UUID) -> Batch:
    """Get batch by ID with product (and category/brand) and supplier loaded."""
    result = await session.execute(
        select(Batch)
        .options(
            joinedload(Batch.product).joinedload(Product.category),
            joinedload(Batch.product).joinedload(Product.brand),
            joinedload(Batch.supplier),
        )
        .where(Batch.id == batch_id)
    )
    batch = result.scalars().unique().first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch with id '{batch_id}' not found.",
        )
    return batch


async def list_batches(
    session: AsyncSession, product_id: Optional[UUID] = None, status_filter: Optional[str] = None
) -> List[Batch]:
    """List batches with optional filters."""
    stmt = select(Batch).options(
        joinedload(Batch.product).joinedload(Product.category),
        joinedload(Batch.product).joinedload(Product.brand),
        joinedload(Batch.supplier),
    )
    if product_id:
        stmt = stmt.where(Batch.product_id == product_id)
    if status_filter:
        stmt = stmt.where(Batch.status == status_filter)

    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def update_batch(session: AsyncSession, batch_id: UUID, data: BatchUpdate) -> Batch:
    """Update batch details (status, notes, dates)."""
    batch = await get_batch_by_id(session, batch_id)

    update_dict = data.model_dump(exclude_unset=True)

    # Validate dates if both present
    m_date = update_dict.get("manufacturing_date", batch.manufacturing_date)
    e_date = update_dict.get("expiry_date", batch.expiry_date)
    if m_date and e_date and e_date < m_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expiry date cannot precede manufacturing date.",
        )

    for key, value in update_dict.items():
        setattr(batch, key, value)

    await session.commit()
    return await get_batch_by_id(session, batch_id)
