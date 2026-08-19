"""
AVENZO Backend — Consumer Recommendations API Endpoints
REST router under /api/v1/recommendations.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User, Role
from app.schemas.recommendation import RecommendationOut, RecommendationSummaryOut
from app.core.dependencies import get_current_user
from app.services.recommendation_service import (
    get_active_recommendations,
    dismiss_recommendation,
    get_consumer_summary,
    generate_and_save_recommendations,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=List[RecommendationOut])
async def list_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve active non-dismissed recommendations for authenticated consumer."""
    return await get_active_recommendations(db, current_user.id)


@router.get("/summary", response_model=RecommendationSummaryOut)
async def get_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve aggregate consumer intelligence summary."""
    return await get_consumer_summary(db, current_user.id)


@router.post("/{recommendation_id}/dismiss", response_model=RecommendationOut)
async def dismiss(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss a recommendation, enforcing consumer ownership isolation."""
    rec = await dismiss_recommendation(db, recommendation_id, current_user.id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found or access denied.",
        )
    return rec


@router.post("/refresh", response_model=List[RecommendationOut])
async def refresh_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger recommendation generation and return updated list."""
    recs = await generate_and_save_recommendations(db, current_user.id)
    return [r for r in recs if not r.is_dismissed]
