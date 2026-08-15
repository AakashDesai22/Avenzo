"""
AVENZO Backend — Warehouse API Router (/api/v1/warehouses)
Multi-warehouse management and location creation.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseRead,
    WarehouseUpdate,
    WarehouseLocationCreate,
    WarehouseLocationRead,
)
from app.schemas.common import ApiResponse
from app.services import warehouse_service

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


@router.get("", response_model=ApiResponse[List[WarehouseRead]])
async def list_warehouses(
    active_only: bool = True,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    List all warehouse facilities.
    """
    warehouses = await warehouse_service.list_warehouses(session, active_only=active_only)
    return ApiResponse(
        success=True,
        data=[WarehouseRead.model_validate(w) for w in warehouses],
    )


@router.get("/{warehouse_id}", response_model=ApiResponse[WarehouseRead])
async def get_warehouse(
    warehouse_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Get warehouse details and bin locations by ID.
    """
    warehouse = await warehouse_service.get_warehouse_by_id(session, warehouse_id)
    return ApiResponse(success=True, data=WarehouseRead.model_validate(warehouse))


@router.post("", response_model=ApiResponse[WarehouseRead], status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    data: WarehouseCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Create a new warehouse facility (Admin/Manager only).
    """
    warehouse = await warehouse_service.create_warehouse(session, data)
    return ApiResponse(
        success=True,
        data=WarehouseRead.model_validate(warehouse),
        message="Warehouse created successfully.",
    )


@router.put("/{warehouse_id}", response_model=ApiResponse[WarehouseRead])
async def update_warehouse(
    warehouse_id: UUID,
    data: WarehouseUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Update warehouse details (Admin/Manager only).
    """
    warehouse = await warehouse_service.update_warehouse(session, warehouse_id, data)
    return ApiResponse(
        success=True,
        data=WarehouseRead.model_validate(warehouse),
        message="Warehouse updated successfully.",
    )


@router.post("/{warehouse_id}/locations", response_model=ApiResponse[WarehouseLocationRead], status_code=status.HTTP_201_CREATED)
async def add_location(
    warehouse_id: UUID,
    data: WarehouseLocationCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Add a bin/location to a warehouse (Admin/Manager only).
    """
    location = await warehouse_service.add_warehouse_location(session, warehouse_id, data)
    return ApiResponse(
        success=True,
        data=WarehouseLocationRead.model_validate(location),
        message="Warehouse location created successfully.",
    )
