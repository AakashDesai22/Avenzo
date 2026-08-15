"""
AVENZO Backend — Supplier API Router (/api/v1/suppliers)
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.schemas.common import ApiResponse
from app.services import supplier_service

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("", response_model=ApiResponse[List[SupplierRead]])
async def list_suppliers(
    active_only: bool = True,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    List all suppliers.
    """
    suppliers = await supplier_service.list_suppliers(session, active_only=active_only)
    return ApiResponse(
        success=True,
        data=[SupplierRead.model_validate(s) for s in suppliers],
    )


@router.get("/{supplier_id}", response_model=ApiResponse[SupplierRead])
async def get_supplier(
    supplier_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Get supplier details by ID.
    """
    supplier = await supplier_service.get_supplier_by_id(session, supplier_id)
    return ApiResponse(success=True, data=SupplierRead.model_validate(supplier))


@router.post("", response_model=ApiResponse[SupplierRead], status_code=status.HTTP_201_CREATED)
async def create_supplier(
    data: SupplierCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Create a supplier master record (Admin/Manager only).
    """
    supplier = await supplier_service.create_supplier(session, data)
    return ApiResponse(
        success=True,
        data=SupplierRead.model_validate(supplier),
        message="Supplier created successfully.",
    )


@router.put("/{supplier_id}", response_model=ApiResponse[SupplierRead])
async def update_supplier(
    supplier_id: UUID,
    data: SupplierUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Update supplier master details (Admin/Manager only).
    """
    supplier = await supplier_service.update_supplier(session, supplier_id, data)
    return ApiResponse(
        success=True,
        data=SupplierRead.model_validate(supplier),
        message="Supplier updated successfully.",
    )
