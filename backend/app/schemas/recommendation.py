"""
AVENZO Backend — Recommendation Schemas
Pydantic response models for consumer recommendations and intelligence summaries.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class RecommendationOut(BaseModel):
    """Schema representing an individual consumer recommendation."""
    id: uuid.UUID
    user_id: uuid.UUID
    pantry_item_id: Optional[uuid.UUID] = None
    recommendation_type: str
    priority: str
    title: str
    message: str
    reason: str
    suggested_action: Optional[str] = None
    metadata_json: Optional[str] = None
    is_dismissed: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationSummaryOut(BaseModel):
    """Schema representing aggregate consumer intelligence summary."""
    total_active_items: int
    expiring_3d_count: int
    expiring_7d_count: int
    estimated_waste_risk_count: int
    has_sufficient_history: bool
    history_status: str

    model_config = ConfigDict(from_attributes=True)
