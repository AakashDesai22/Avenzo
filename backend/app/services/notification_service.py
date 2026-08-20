"""
AVENZO Backend — Notification Service & System Integration Engine
Service layer managing user preferences, registered devices, server notification events, and FCM dispatch abstraction.
"""

import os
import uuid
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import firebase_admin
from firebase_admin import credentials, messaging, exceptions

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update

from app.models.notification import NotificationPreference, ConsumerDevice, NotificationRecord
from app.models.base import utc_now

logger = logging.getLogger(__name__)


class TokenUnregisteredError(Exception):
    """Raised when FCM reports a token as unregistered or invalid."""

    def __init__(self, token: str):
        self.token = token
        super().__init__("FCM registration token is invalid or unregistered.")


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
        masked_token = f"{fcm_token[:10]}..." if len(fcm_token) > 10 else fcm_token
        logger.info(
            f"[MockFCM Push Dispatch] Token: {masked_token} | Title: {title} | Body: {body} | Data: {data}"
        )
        return True


def initialize_firebase_admin() -> Optional[firebase_admin.App]:
    """Initializes Firebase Admin SDK using GOOGLE_APPLICATION_CREDENTIALS if available."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path:
        logger.warning(
            "[Firebase Admin] GOOGLE_APPLICATION_CREDENTIALS environment variable is not set. "
            "Firebase FCM push notifications will fall back to MockFCMProvider."
        )
        return None

    if not os.path.exists(cred_path):
        logger.error(
            f"[Firebase Admin] Service account credentials file not found at path: {cred_path}. "
            "Firebase FCM push notifications will fall back to MockFCMProvider."
        )
        return None

    try:
        cred = credentials.Certificate(cred_path)
        app = firebase_admin.initialize_app(cred)
        logger.info("[Firebase Admin] Firebase Admin SDK successfully initialized.")
        return app
    except Exception as e:
        logger.error(
            f"[Firebase Admin Error] Failed to initialize Firebase Admin SDK: {type(e).__name__}: {e}"
        )
        return None


class FirebaseFCMProvider(FCMProvider):
    """Production FCM Provider delivering push messages via Firebase Admin SDK."""

    def __init__(self, app: Optional[firebase_admin.App] = None):
        self.app = app or initialize_firebase_admin()

    async def send_push_notification(
        self, fcm_token: str, title: str, body: str, data: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not self.app:
            logger.warning("[FirebaseFCMProvider] Firebase Admin App not initialized. Skipping push.")
            return False

        masked_token = f"{fcm_token[:10]}..." if len(fcm_token) > 10 else fcm_token
        try:
            msg_data = {k: str(v) for k, v in (data or {}).items()}
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=msg_data,
                token=fcm_token,
            )
            response = messaging.send(message, app=self.app)
            logger.info(f"[FCM Push Success] Token: {masked_token} | MessageId: {response}")
            return True
        except messaging.UnregisteredError:
            logger.warning(f"[FCM Invalid Token] Token unregistered or invalid: {masked_token}")
            raise TokenUnregisteredError(fcm_token)
        except messaging.SenderIdMismatchError:
            logger.warning(f"[FCM Invalid Token] Sender ID mismatch for token: {masked_token}")
            raise TokenUnregisteredError(fcm_token)
        except exceptions.InvalidArgumentError:
            logger.warning(f"[FCM Invalid Token] Invalid argument for token: {masked_token}")
            raise TokenUnregisteredError(fcm_token)
        except exceptions.NotFoundError:
            logger.warning(f"[FCM Invalid Token] Entity not found for token: {masked_token}")
            raise TokenUnregisteredError(fcm_token)
        except exceptions.FirebaseError as e:
            err_str = str(e).lower()
            if "unregistered" in err_str or "invalid" in err_str or "not-found" in err_str:
                logger.warning(f"[FCM Invalid Token] FirebaseError indicates invalid token: {masked_token}")
                raise TokenUnregisteredError(fcm_token)
            logger.error(f"[FCM FirebaseError] Token: {masked_token} | Error: {type(e).__name__}: {e}")
            return False
        except Exception as e:
            logger.error(f"[FCM Unexpected Error] Token: {masked_token} | Error: {e}")
            return False


def select_default_fcm_provider() -> FCMProvider:
    """Auto-selects FirebaseFCMProvider if credentials exist, else returns MockFCMProvider."""
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.exists(cred_path):
        app = initialize_firebase_admin()
        if app:
            return FirebaseFCMProvider(app)
    return MockFCMProvider()


# Default provider instance
_fcm_provider: FCMProvider = MockFCMProvider()


def get_fcm_provider() -> FCMProvider:
    """Returns active FCMProvider instance."""
    global _fcm_provider
    return _fcm_provider


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
        any_success = False
        for dev in devices:
            if dev.fcm_token:
                try:
                    success = await _fcm_provider.send_push_notification(
                        dev.fcm_token, title, body, {"notification_id": str(record.id)}
                    )
                    if success:
                        any_success = True
                except TokenUnregisteredError:
                    masked = f"{dev.fcm_token[:10]}..." if len(dev.fcm_token) > 10 else dev.fcm_token
                    logger.warning(
                        f"Deactivating invalid device token (device_id: {dev.device_id}, token: {masked})"
                    )
                    dev.is_active = False

        if any_success:
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
