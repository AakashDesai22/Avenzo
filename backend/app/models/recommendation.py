"""
AVENZO Backend — Consumer Recommendation Model
ORM entity storing personalized consumption insights and smart pantry recommendations.
"""

from sqlalchemy import Column, String, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin, utc_now


class ConsumerRecommendation(Base, UUIDMixin, TimestampMixin):
    """ORM model representing an actionable, explainable recommendation for a consumer."""
    __tablename__ = "consumer_recommendations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    pantry_item_id = Column(UUID(as_uuid=True), ForeignKey("pantry_items.id"), nullable=True, index=True)
    recommendation_type = Column(String(50), nullable=False, index=True)
    # Types: USE_SOON, WASTE_RISK, OVERSTOCK, CONSUMPTION_INSIGHT, EXPIRY_PRIORITY, SMART_ACTION
    priority = Column(String(30), nullable=False, default="MEDIUM", index=True)
    # Priorities: CRITICAL, HIGH, MEDIUM, LOW
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    suggested_action = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=True)
    is_dismissed = Column(Boolean, nullable=False, default=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    pantry_item = relationship("PantryItem")
