"""
AVENZO Backend — Notification Models
ORM entities for user preferences, registered consumer devices, and server-side notification records.
"""

from sqlalchemy import Column, String, ForeignKey, Text, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin, utc_now


class NotificationPreference(Base, UUIDMixin, TimestampMixin):
    """Consumer user notification preferences and configuration."""
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_notification_preferences"),
    )

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expiry_alerts = Column(Boolean, nullable=False, default=True)
    critical_expiry_alerts = Column(Boolean, nullable=False, default=True)
    pantry_updates = Column(Boolean, nullable=False, default=True)
    recommendation_alerts = Column(Boolean, nullable=False, default=True)
    quiet_hours_enabled = Column(Boolean, nullable=False, default=False)
    quiet_hours_start = Column(String(10), nullable=True, default="22:00")
    quiet_hours_end = Column(String(10), nullable=True, default="07:00")

    user = relationship("User")


class ConsumerDevice(Base, UUIDMixin, TimestampMixin):
    """Consumer registered device for push notifications (FCM tokens)."""
    __tablename__ = "consumer_devices"
    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_user_device"),
    )

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(30), nullable=False, default="android")  # android, ios, web
    fcm_token = Column(String(500), nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_active_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User")


class NotificationRecord(Base, UUIDMixin, TimestampMixin):
    """Server-side notification event persistence log and lifecycle tracking."""
    __tablename__ = "notification_records"
    __table_args__ = (
        Index("ix_notification_user_type_ref", "user_id", "notification_type", "reference_type", "reference_id"),
    )

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    # Types: EXPIRY_7_DAY, EXPIRY_3_DAY, EXPIRY_TODAY, PRODUCT_EXPIRED, PANTRY_UPDATE, RECOMMENDATION, SYSTEM, BATCH_RECALL
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    payload_json = Column(Text, nullable=True)
    reference_type = Column(String(50), nullable=True, index=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    status = Column(String(30), nullable=False, default="CREATED", index=True)
    # Statuses: CREATED, SCHEDULED, SENT, DELIVERED, READ, FAILED
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
