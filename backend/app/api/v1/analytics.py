"""
AVENZO Backend — Closed-Loop Analytics API Endpoints (/api/v1/analytics)
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.analytics import ConsumerWasteMetricsRead, BusinessWasteAnalyticsRead
from app.schemas.common import ApiResponse
from app.services import waste_analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics & Closed-Loop Waste"])


@router.get("/consumer", response_model=ApiResponse[ConsumerWasteMetricsRead])
async def get_consumer_waste_analytics(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Get personal waste reduction metrics, consumption ratio, and Waste Reduction Index.
    Strictly scoped to the current authenticated consumer user ID.
    """
    metrics = await waste_analytics_service.get_consumer_waste_analytics(
        session, user_id=current_user.id
    )
    return ApiResponse(success=True, data=metrics)


@router.get("/business/waste", response_model=ApiResponse[BusinessWasteAnalyticsRead])
async def get_business_waste_analytics(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "BUSINESS_MANAGER", "STAFF"])),
):
    """
    Get aggregate, privacy-safe business inventory waste metrics, consumer discard feedback,
    and top spoilage product lists. Excludes all consumer personal identifying data.
    """
    analytics = await waste_analytics_service.get_business_waste_analytics(session)
    return ApiResponse(success=True, data=analytics)
