"""
AVENZO Backend — Supplier Service
Business logic for managing Supplier master entities.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


async def create_supplier(session: AsyncSession, data: SupplierCreate) -> Supplier:
    """Create a supplier master entity."""
    supplier = Supplier(
        name=data.name,
        contact_person=data.contact_person,
        email=data.email,
        phone=data.phone,
        address=data.address,
        city=data.city,
        country=data.country,
        is_active=data.is_active,
    )
    session.add(supplier)
    await session.commit()
    await session.refresh(supplier)
    return supplier


async def get_supplier_by_id(session: AsyncSession, supplier_id: UUID) -> Supplier:
    """Get supplier by ID."""
    result = await session.execute(
        select(Supplier).where(Supplier.id == supplier_id, Supplier.is_deleted == False)
    )
    supplier = result.scalars().first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id '{supplier_id}' not found.",
        )
    return supplier


async def list_suppliers(session: AsyncSession, active_only: bool = True) -> List[Supplier]:
    """List suppliers."""
    stmt = select(Supplier).where(Supplier.is_deleted == False)
    if active_only:
        stmt = stmt.where(Supplier.is_active == True)
    result = await session.execute(stmt)
    return result.scalars().all()


async def update_supplier(session: AsyncSession, supplier_id: UUID, data: SupplierUpdate) -> Supplier:
    """Update supplier properties."""
    supplier = await get_supplier_by_id(session, supplier_id)
    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(supplier, key, value)
    await session.commit()
    await session.refresh(supplier)
    return supplier
