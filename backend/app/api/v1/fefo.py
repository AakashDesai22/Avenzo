"""
AVENZO Backend — FEFO Intelligence API Router (/api/v1/fefo)
FEFO batch ranking, read-only allocation preview, and violation verification.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.fefo import (
    FEFORankedBatchRead,
    FEFOAllocationRequest,
    FEFOAllocationPlanResponse,
    FEFOVerificationRequest,
    FEFOVerificationResponse,
)
from app.schemas.common import ApiResponse
from app.services import fefo_service

router = APIRouter(prefix="/fefo", tags=["FEFO Intelligence"])


@router.get("/batches", response_model=ApiResponse[List[FEFORankedBatchRead]])
async def list_fefo_ranked_batches(
    product_id: UUID = Query(..., description="Target product UUID"),
    warehouse_id: Optional[UUID] = Query(None, description="Optional warehouse filter"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    List pickable inventory batches for a product strictly ranked by FEFO rules:
    1. expiry_date ASC, 2. mfg_date ASC, 3. created_at ASC, 4. quantity_available DESC, 5. batch.id ASC.
    """
    ranked_batches = await fefo_service.get_fefo_ranked_batches(session, product_id, warehouse_id)
    return ApiResponse(
        success=True,
        data=ranked_batches,
    )


@router.post("/allocate", response_model=ApiResponse[FEFOAllocationPlanResponse])
async def preview_fefo_allocation(
    request: FEFOAllocationRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    READ-ONLY FEFO Allocation Preview.
    Calculates stock pick allocations for the requested quantity using FEFO rules.
    MUST NOT reserve inventory, mutate stock balances, or write database state.
    """
    plan = await fefo_service.generate_allocation_preview(
        session, request.product_id, request.requested_quantity, request.warehouse_id
    )
    return ApiResponse(
        success=True,
        data=plan,
        message="FEFO allocation preview generated.",
    )


@router.post("/verify-selection", response_model=ApiResponse[FEFOVerificationResponse])
async def verify_fefo_selection(
    request: FEFOVerificationRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Evaluates whether selecting selected_batch_id constitutes a FEFO violation.
    If earlier-expiring available stock was bypassed, returns a warning and records an audit log.
    Non-blocking decision support behavior.
    """
    result = await fefo_service.verify_selection_and_audit(
        session=session,
        product_id=request.product_id,
        selected_batch_id=request.selected_batch_id,
        requested_quantity=request.requested_quantity,
        warehouse_id=request.warehouse_id,
        override_reason=request.override_reason,
        performed_by_id=current_user.id,
    )
    return ApiResponse(
        success=True,
        data=result,
        message="FEFO selection verified." if result.is_compliant else "FEFO violation warning generated.",
    )
