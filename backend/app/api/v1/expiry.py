"""
AVENZO Backend — Expiry Intelligence and Risk API Router (/api/v1/inventory)
Expiry summaries and deterministic inventory risk metrics.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.expiry import ExpirySummaryResponse, InventoryRiskMetricsResponse
from app.schemas.common import ApiResponse
from app.services import expiry_service

router = APIRouter(prefix="/inventory", tags=["Expiry Intelligence & Risk"])


@router.get("/expiry-summary", response_model=ApiResponse[ExpirySummaryResponse])
async def get_expiry_summary(
    warehouse_id: Optional[UUID] = Query(None, description="Filter by warehouse"),
    category_id: Optional[UUID] = Query(None, description="Filter by category"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Get aggregated inventory stock breakdown by expiry classification (SAFE, EXPIRING_SOON, CRITICAL, EXPIRED, N/A).
    """
    summary = await expiry_service.get_expiry_summary(
        session, warehouse_id=warehouse_id, category_id=category_id
    )
    return ApiResponse(
        success=True,
        data=summary,
    )


@router.get("/risk-metrics", response_model=ApiResponse[InventoryRiskMetricsResponse])
async def get_inventory_risk_metrics(
    warehouse_id: Optional[UUID] = Query(None, description="Filter by warehouse"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER"])),
):
    """
    Get deterministic inventory risk indicators:
    - Near-expiry stock & expired stock quantities
    - Expiry exposure percentage
    - Capital Exposure at Risk (sum of qty * product.cost_price for DTE <= 30)
    - Potential Sales Exposure (sum of qty * product.unit_price for DTE <= 30)
    """
    metrics = await expiry_service.get_risk_metrics(session, warehouse_id=warehouse_id)
    return ApiResponse(
        success=True,
        data=metrics,
    )
