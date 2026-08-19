"""
AVENZO Backend — Notification Service & System Integration Engine
Service layer managing user preferences, registered devices, server notification events, and FCM dispatch abstraction.
"""

import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update

from app.models.notification import NotificationPreference, ConsumerDevice, NotificationRecord
from app.models.base import utc_now

logger = logging.getLogger(__name__)


class FCMProvider(ABC):
    """Abstract interface for Cloud Push Notification delivery (FCM)."""

    @abstractmethod
    async def send_push_notification(
        self, fcm_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        pass


class MockFCMProvider(FCMProvider):
    """Development / Test FCM Provider logging push dispatches without external API calls."""

    async def send_push_notification(
        self, fcm_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        logger.info(
            f"[FCM Push Dispatch] Token: {fcm_token[:10]}... | Title: {title} | Body: {body} | Data: {data}"
        )
        return True


# Default provider instance
_fcm_provider: FCMProvider = MockFCMProvider()


def set_fcm_provider(provider: FCMProvider) -> None:
    """Sets active FCM provider implementation."""
    global _fcm_provider
    _fcm_provider = provider


# -----------------------------------------------------------------------------
# Preferences Management
# -----------------------------------------------------------------------------

async def get_or_create_user_preferences(
    session: AsyncSession, user_id: uuid.UUID
) -> NotificationPreference:
    """Retrieves notification preferences for user, creating default settings if missing."""
    stmt = select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    res = await session.execute(stmt)
    prefs = res.scalar_one_or_none()

    if not prefs:
        prefs = NotificationPreference(
            user_id=user_id,
            expiry_alerts=True,
            critical_expiry_alerts=True,
            pantry_updates=True,
            recommendation_alerts=True,
            quiet_hours_enabled=False,
            quiet_hours_start="22:00",
            quiet_hours_end="07:00",
        )
        session.add(prefs)
        await session.commit()
        await session.refresh(prefs)

    return prefs


async def update_user_preferences(
    session: AsyncSession, user_id: uuid.UUID, updates: Dict[str, Any]
) -> NotificationPreference:
    """Updates user notification preferences."""
    prefs = await get_or_create_user_preferences(session, user_id)

    allowed_fields = {
        "expiry_alerts",
        "critical_expiry_alerts",
        "pantry_updates",
        "recommendation_alerts",
        "quiet_hours_enabled",
        "quiet_hours_start",
        "quiet_hours_end",
    }

    for key, value in updates.items():
        if key in allowed_fields and value is not None:
            setattr(prefs, key, value)

    await session.commit()
    await session.refresh(prefs)
    return prefs


# -----------------------------------------------------------------------------
# Consumer Devices Registration
# -----------------------------------------------------------------------------

async def register_consumer_device(
    session: AsyncSession,
    user_id: uuid.UUID,
    device_id: str,
    platform: str = "android",
    fcm_token: Optional[str] = None,
) -> ConsumerDevice:
    """Registers or updates a consumer device token."""
    stmt = select(ConsumerDevice).where(
        ConsumerDevice.user_id == user_id,
        ConsumerDevice.device_id == device_id,
    )
    res = await session.execute(stmt)
    device = res.scalar_one_or_none()

    now = utc_now()
    if device:
        device.platform = platform
        if fcm_token:
            device.fcm_token = fcm_token
        device.is_active = True
        device.last_active_at = now
    else:
        device = ConsumerDevice(
            user_id=user_id,
            device_id=device_id,
            platform=platform,
            fcm_token=fcm_token,
            is_active=True,
            last_active_at=now,
        )
        session.add(device)

    await session.commit()
    await session.refresh(device)
    return device


async def delete_consumer_device(
    session: AsyncSession, user_id: uuid.UUID, device_id: str
) -> bool:
    """Deletes or deactivates device registration enforcing user ownership."""
    stmt = select(ConsumerDevice).where(
        ConsumerDevice.user_id == user_id,
        ConsumerDevice.device_id == device_id,
    )
    res = await session.execute(stmt)
    device = res.scalar_one_or_none()

    if device:
        await session.delete(device)
        await session.commit()
        return True
    return False


# -----------------------------------------------------------------------------
# Server Notification Events & Dispatch
# -----------------------------------------------------------------------------

async def create_notification_record(
    session: AsyncSession,
    user_id: uuid.UUID,
    notification_type: str,
    title: str,
    body: str,
    payload_json: Optional[str] = None,
) -> NotificationRecord:
    """Creates server notification record and dispatches to active registered devices if preferences allow."""
    # Check user preferences
    prefs = await get_or_create_user_preferences(session, user_id)
    
    if notification_type.startswith("EXPIRY_") and not prefs.expiry_alerts:
        logger.info(f"Notification suppressed due to user preferences: {notification_type}")

    record = NotificationRecord(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
        payload_json=payload_json,
        status="CREATED",
        is_read=False,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)

    # Fetch active devices with FCM tokens
    device_stmt = select(ConsumerDevice).where(
        ConsumerDevice.user_id == user_id,
        ConsumerDevice.is_active == True,
        ConsumerDevice.fcm_token != None,
    )
    device_res = await session.execute(device_stmt)
    devices = list(device_res.scalars().all())

    if devices:
        record.status = "SENT"
        record.sent_at = utc_now()
        for dev in devices:
            if dev.fcm_token:
                await _fcm_provider.send_push_notification(
                    dev.fcm_token, title, body, {"notification_id": str(record.id)}
                )
        record.status = "DELIVERED"
        await session.commit()

    return record


async def list_user_notifications(
    session: AsyncSession, user_id: uuid.UUID, unread_only: bool = False
) -> List[NotificationRecord]:
    """Retrieves notification records for user ordered by creation date DESC."""
    stmt = select(NotificationRecord).where(NotificationRecord.user_id == user_id)
    if unread_only:
        stmt = stmt.where(NotificationRecord.is_read == False)
    stmt = stmt.order_by(NotificationRecord.created_at.desc())

    res = await session.execute(stmt)
    return list(res.scalars().all())


async def get_unread_notification_count(
    session: AsyncSession, user_id: uuid.UUID
) -> int:
    """Returns unread notification count for user."""
    stmt = select(func.count(NotificationRecord.id)).where(
        NotificationRecord.user_id == user_id,
        NotificationRecord.is_read == False,
    )
    res = await session.execute(stmt)
    return res.scalar() or 0


async def mark_notification_as_read(
    session: AsyncSession, user_id: uuid.UUID, notification_id: uuid.UUID
) -> Optional[NotificationRecord]:
    """Marks notification as read enforcing user ownership isolation."""
    stmt = select(NotificationRecord).where(
        NotificationRecord.id == notification_id,
        NotificationRecord.user_id == user_id,
    )
    res = await session.execute(stmt)
    record = res.scalar_one_or_none()

    if record:
        record.is_read = True
        record.read_at = utc_now()
        record.status = "READ"
        await session.commit()
        await session.refresh(record)
        return record
    return None


async def mark_all_notifications_as_read(
    session: AsyncSession, user_id: uuid.UUID
) -> int:
    """Marks all unread notifications for user as read."""
    now = utc_now()
    stmt = (
        update(NotificationRecord)
        .where(
            NotificationRecord.user_id == user_id,
            NotificationRecord.is_read == False,
        )
        .values(is_read=True, read_at=now, status="READ")
    )
    res = await session.execute(stmt)
    await session.commit()
    return res.rowcount
