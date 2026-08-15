"""
AVENZO Backend — Inventory API Router (/api/v1/inventory)
Stock level tracking and transaction audit logs.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.inventory import InventoryRead, InventoryAdjustRequest, InventoryTransactionRead
from app.schemas.common import ApiResponse
from app.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=ApiResponse[List[InventoryRead]])
async def list_inventory(
    warehouse_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    batch_id: Optional[UUID] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    List inventory balances with optional warehouse, product, or batch filtering.
    """
    inventories = await inventory_service.list_inventory(
        session, warehouse_id=warehouse_id, product_id=product_id, batch_id=batch_id
    )
    return ApiResponse(
        success=True,
        data=[InventoryRead.model_validate(inv) for inv in inventories],
    )


@router.get("/transactions", response_model=ApiResponse[List[InventoryTransactionRead]])
async def list_transactions(
    inventory_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    List audit log transactions for stock movements.
    """
    transactions = await inventory_service.list_transactions(
        session, inventory_id=inventory_id, skip=skip, limit=limit
    )
    return ApiResponse(
        success=True,
        data=[InventoryTransactionRead.model_validate(tx) for tx in transactions],
    )


@router.get("/{inventory_id}", response_model=ApiResponse[InventoryRead])
async def get_inventory(
    inventory_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Get inventory balance details by ID.
    """
    inventory = await inventory_service.get_inventory_by_id(session, inventory_id)
    return ApiResponse(success=True, data=InventoryRead.model_validate(inventory))


@router.post("/adjust", response_model=ApiResponse[InventoryRead], status_code=status.HTTP_200_OK)
async def adjust_inventory(
    request: InventoryAdjustRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Adjust stock level (addition or reduction) and record an Inventory Transaction audit log.
    """
    inventory = await inventory_service.adjust_inventory(
        session, request, performed_by_id=current_user.id
    )
    return ApiResponse(
        success=True,
        data=InventoryRead.model_validate(inventory),
        message=f"Stock successfully adjusted ({request.quantity_change}).",
    )
