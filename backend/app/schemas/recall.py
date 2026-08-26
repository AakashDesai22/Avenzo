"""
AVENZO Backend — Batch Recall Schemas
"""

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BatchRecallRequest(BaseModel):
    recall_reason: str = Field(..., min_length=3, max_length=1000)
    severity: Optional[str] = Field("HIGH", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")


class BatchRecallImpactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    batch_id: UUID
    batch_number: str
    product_id: UUID
    product_name: str
    is_already_recalled: bool = False
    affected_orders_count: int
    affected_consumers_count: int
    affected_pantry_items_count: int
    notifications_sent_count: int
    recalled_at: Optional[datetime] = None
    recall_reason: Optional[str] = None
