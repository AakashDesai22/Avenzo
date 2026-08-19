"""
AVENZO Backend — Notifications API Endpoints
REST router under /api/v1/notifications.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
    ConsumerDeviceRegister,
    ConsumerDeviceOut,
    NotificationRecordOut,
    UnreadCountOut,
)
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/preferences", response_model=NotificationPreferenceOut)
async def get_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve notification preferences for current user."""
    return await notification_service.get_or_create_user_preferences(db, current_user.id)


@router.put("/preferences", response_model=NotificationPreferenceOut)
async def update_preferences(
    payload: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update notification preferences for current user."""
    return await notification_service.update_user_preferences(
        db, current_user.id, payload.model_dump(exclude_unset=True)
    )


@router.post("/devices", response_model=ConsumerDeviceOut, status_code=status.HTTP_201_CREATED)
async def register_device(
    payload: ConsumerDeviceRegister,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register or update a consumer device token."""
    return await notification_service.register_consumer_device(
        db,
        current_user.id,
        payload.device_id,
        payload.platform,
        payload.fcm_token,
    )


@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_device(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove registered consumer device token enforcing user ownership."""
    success = await notification_service.delete_consumer_device(db, current_user.id, device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device registration not found.",
        )


@router.get("", response_model=List[NotificationRecordOut])
async def list_notifications(
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve notifications list for current authenticated user."""
    return await notification_service.list_user_notifications(db, current_user.id, unread_only)


@router.get("/unread-count", response_model=UnreadCountOut)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve unread notification count for current authenticated user."""
    count = await notification_service.get_unread_notification_count(db, current_user.id)
    return UnreadCountOut(unread_count=count)


@router.post("/{notification_id}/read", response_model=NotificationRecordOut)
async def mark_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a notification as read, enforcing user ownership isolation."""
    record = await notification_service.mark_notification_as_read(db, current_user.id, notification_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied.",
        )
    return record


@router.post("/read-all", response_model=UnreadCountOut)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all unread notifications for current user as read."""
    await notification_service.mark_all_notifications_as_read(db, current_user.id)
    return UnreadCountOut(unread_count=0)
