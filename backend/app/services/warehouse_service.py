"""
AVENZO Backend — Warehouse Service
Business logic for managing Warehouses and Warehouse Locations.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from app.models.warehouse import Warehouse, WarehouseLocation
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseLocationCreate


async def create_warehouse(session: AsyncSession, data: WarehouseCreate) -> Warehouse:
    """Create a new warehouse facility."""
    warehouse = Warehouse(
        name=data.name,
        address=data.address,
        city=data.city,
        is_active=data.is_active,
    )
    session.add(warehouse)
    await session.commit()
    return await get_warehouse_by_id(session, warehouse.id)


async def get_warehouse_by_id(session: AsyncSession, warehouse_id: UUID) -> Warehouse:
    """Get warehouse by ID with locations loaded."""
    result = await session.execute(
        select(Warehouse)
        .options(joinedload(Warehouse.locations))
        .where(Warehouse.id == warehouse_id)
    )
    warehouse = result.scalars().unique().first()
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse with id '{warehouse_id}' not found.",
        )
    return warehouse


async def list_warehouses(session: AsyncSession, active_only: bool = True) -> List[Warehouse]:
    """List warehouses."""
    stmt = select(Warehouse).options(joinedload(Warehouse.locations))
    if active_only:
        stmt = stmt.where(Warehouse.is_active == True)
    result = await session.execute(stmt)
    return result.scalars().unique().all()


async def update_warehouse(session: AsyncSession, warehouse_id: UUID, data: WarehouseUpdate) -> Warehouse:
    """Update warehouse properties."""
    warehouse = await get_warehouse_by_id(session, warehouse_id)
    update_dict = data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(warehouse, key, value)
    await session.commit()
    return await get_warehouse_by_id(session, warehouse_id)


async def add_warehouse_location(
    session: AsyncSession, warehouse_id: UUID, data: WarehouseLocationCreate
) -> WarehouseLocation:
    """Add a location/bin to a warehouse."""
    warehouse = await get_warehouse_by_id(session, warehouse_id)

    # Check for duplicate location_code in this warehouse
    loc_res = await session.execute(
        select(WarehouseLocation).where(
            WarehouseLocation.warehouse_id == warehouse_id,
            WarehouseLocation.location_code == data.location_code,
        )
    )
    if loc_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Location code '{data.location_code}' already exists in warehouse '{warehouse.name}'.",
        )

    location = WarehouseLocation(
        warehouse_id=warehouse_id,
        location_code=data.location_code,
        description=data.description,
        is_active=data.is_active,
    )
    session.add(location)
    await session.commit()
    await session.refresh(location)
    return location
