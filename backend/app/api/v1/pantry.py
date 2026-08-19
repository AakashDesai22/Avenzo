"""
AVENZO Backend — Consumer Digital Pantry API Router (/api/v1/pantry)
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.pantry import (
    PantryItemCreate,
    PantryItemUpdate,
    PantryItemRead,
    PantryItemActionRequest,
)
from app.schemas.common import ApiResponse
from app.services import pantry_service

router = APIRouter(prefix="/pantry", tags=["Digital Pantry"])


@router.get("", response_model=ApiResponse[List[PantryItemRead]])
async def list_pantry_items(
    pantry_id: Optional[UUID] = None,
    storage_location: Optional[str] = Query(None, pattern="^(pantry|fridge|freezer)$"),
    status_filter: str = Query("active", alias="status"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List active pantry items for the current authenticated consumer.
    """
    items = await pantry_service.list_pantry_items(
        session,
        user_id=current_user.id,
        pantry_id=pantry_id,
        storage_location=storage_location,
        status_filter=status_filter,
    )
    return ApiResponse(success=True, data=items)


@router.post("", response_model=ApiResponse[PantryItemRead], status_code=status.HTTP_201_CREATED)
async def create_pantry_item(
    data: PantryItemCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add a new product or custom item to consumer's digital pantry.
    """
    item = await pantry_service.create_pantry_item(session, user_id=current_user.id, data=data)
    return ApiResponse(
        success=True,
        data=item,
        message="Item added to digital pantry successfully.",
    )


@router.get("/expiring", response_model=ApiResponse[List[PantryItemRead]])
async def list_expiring_pantry_items(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List active consumer pantry items with valid expiry dates sorted by DTE ASC.
    """
    items = await pantry_service.list_expiring_pantry_items(session, user_id=current_user.id)
    return ApiResponse(success=True, data=items)


@router.get("/{item_id}", response_model=ApiResponse[PantryItemRead])
async def get_pantry_item(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get pantry item details by ID (enforces ownership isolation).
    """
    item = await pantry_service.get_pantry_item(session, user_id=current_user.id, item_id=item_id)
    return ApiResponse(success=True, data=pantry_service._enrich_item_read(item))


@router.put("/{item_id}", response_model=ApiResponse[PantryItemRead])
async def update_pantry_item(
    item_id: UUID,
    data: PantryItemUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update pantry item details or adjust quantity.
    """
    item = await pantry_service.update_pantry_item(
        session, user_id=current_user.id, item_id=item_id, data=data
    )
    return ApiResponse(
        success=True,
        data=item,
        message="Pantry item updated successfully.",
    )


@router.delete("/{item_id}", response_model=ApiResponse[PantryItemRead])
async def delete_pantry_item(
    item_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete pantry item.
    """
    item = await pantry_service.delete_pantry_item(session, user_id=current_user.id, item_id=item_id)
    return ApiResponse(
        success=True,
        data=item,
        message="Pantry item removed.",
    )


@router.post("/{item_id}/consume", response_model=ApiResponse[PantryItemRead])
async def consume_pantry_item(
    item_id: UUID,
    request: PantryItemActionRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Consume specified quantity from pantry item.
    """
    item = await pantry_service.consume_pantry_item(
        session, user_id=current_user.id, item_id=item_id, consume_qty=request.quantity
    )
    return ApiResponse(
        success=True,
        data=item,
        message=f"Consumed {request.quantity} {item.unit}.",
    )


@router.post("/{item_id}/discard", response_model=ApiResponse[PantryItemRead])
async def discard_pantry_item(
    item_id: UUID,
    request: PantryItemActionRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Discard/waste specified quantity from pantry item.
    """
    item = await pantry_service.discard_pantry_item(
        session, user_id=current_user.id, item_id=item_id, discard_qty=request.quantity
    )
    return ApiResponse(
        success=True,
        data=item,
        message=f"Discarded {request.quantity} {item.unit}.",
    )
