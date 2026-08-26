"""
AVENZO Backend — Batch API Router (/api/v1/batches)
Batch creation, tracking, and expiry metadata.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.batch import BatchCreate, BatchRead, BatchUpdate
from app.schemas.recall import BatchRecallRequest, BatchRecallImpactResponse
from app.schemas.common import ApiResponse
from app.services import batch_service, recall_service

router = APIRouter(prefix="/batches", tags=["Batches"])


@router.get("", response_model=ApiResponse[List[BatchRead]])
async def list_batches(
    product_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    List batches with optional product and status filters.
    """
    batches = await batch_service.list_batches(session, product_id=product_id, status_filter=status_filter)
    return ApiResponse(
        success=True,
        data=[BatchRead.model_validate(b) for b in batches],
    )


@router.get("/{batch_id}", response_model=ApiResponse[BatchRead])
async def get_batch(
    batch_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Get batch details by ID.
    """
    batch = await batch_service.get_batch_by_id(session, batch_id)
    return ApiResponse(success=True, data=BatchRead.model_validate(batch))


@router.get("/{batch_id}/recall-impact", response_model=ApiResponse[BatchRecallImpactResponse])
async def preview_batch_recall_impact(
    batch_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Preview batch recall impact (affected orders, consumers, and pantry items).
    Available to Admin, Business Manager, and Staff.
    """
    impact = await recall_service.calculate_recall_impact(session, batch_id)
    return ApiResponse(success=True, data=impact)


@router.post("/{batch_id}/recall", response_model=ApiResponse[BatchRecallImpactResponse])
async def recall_batch(
    batch_id: UUID,
    data: BatchRecallRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Execute batch recall operation (Admin and Business Manager only).
    Marks target batch as recalled, flags affected consumer PantryItems, and dispatches safety push alerts.
    """
    impact = await recall_service.recall_batch(session, batch_id, user_id=current_user.id, data=data)
    return ApiResponse(
        success=True,
        data=impact,
        message="Batch recall initiated successfully.",
    )


@router.post("", response_model=ApiResponse[BatchRead], status_code=status.HTTP_201_CREATED)
async def create_batch(
    data: BatchCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Create a new product batch (Admin, Manager, or Staff).
    Validates that expiry date cannot precede manufacturing date.
    """
    batch = await batch_service.create_batch(session, data, created_by_id=current_user.id)
    return ApiResponse(
        success=True,
        data=BatchRead.model_validate(batch),
        message="Batch created successfully.",
    )


@router.put("/{batch_id}", response_model=ApiResponse[BatchRead])
async def update_batch(
    batch_id: UUID,
    data: BatchUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Update batch status, notes, or dates (Admin, Manager, or Staff).
    """
    batch = await batch_service.update_batch(session, batch_id, data)
    return ApiResponse(
        success=True,
        data=BatchRead.model_validate(batch),
        message="Batch updated successfully.",
    )
