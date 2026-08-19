"""
AVENZO Backend — Notification Schemas
Pydantic models for notification preferences, device registration, and notification records.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferenceOut(BaseModel):
    """Schema representing user notification preferences."""
    user_id: uuid.UUID
    expiry_alerts: bool
    critical_expiry_alerts: bool
    pantry_updates: bool
    recommendation_alerts: bool
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "07:00"

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences."""
    expiry_alerts: Optional[bool] = None
    critical_expiry_alerts: Optional[bool] = None
    pantry_updates: Optional[bool] = None
    recommendation_alerts: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class ConsumerDeviceRegister(BaseModel):
    """Schema for registering or updating a consumer device token."""
    device_id: str = Field(..., min_length=1, max_length=100)
    platform: str = Field("android", max_length=30)
    fcm_token: Optional[str] = Field(None, max_length=500)


class ConsumerDeviceOut(BaseModel):
    """Schema representing a registered consumer device."""
    id: uuid.UUID
    user_id: uuid.UUID
    device_id: str
    platform: str
    fcm_token: Optional[str] = None
    is_active: bool
    last_active_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationRecordOut(BaseModel):
    """Schema representing a server notification event."""
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    title: str
    body: str
    payload_json: Optional[str] = None
    status: str
    is_read: bool
    read_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountOut(BaseModel):
    """Schema representing unread notification count."""
    unread_count: int
