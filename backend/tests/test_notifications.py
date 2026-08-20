"""
AVENZO Backend — Notifications & System Integrations Tests
"""

import pytest
import uuid
from unittest.mock import MagicMock, patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from firebase_admin import messaging, exceptions as fb_exceptions

from app.models.notification import NotificationPreference, ConsumerDevice, NotificationRecord
from app.services.notification_service import (
    get_or_create_user_preferences,
    create_notification_record,
    register_consumer_device,
    initialize_firebase_admin,
    select_default_fcm_provider,
    FirebaseFCMProvider,
    MockFCMProvider,
    FCMProvider,
    TokenUnregisteredError,
    set_fcm_provider,
    get_fcm_provider,
)
from app.core.security import create_access_token
from tests.conftest import _create_test_user_with_role


@pytest.mark.asyncio
async def test_notification_preferences_flow(client: AsyncClient, db_session: AsyncSession):
    """Verifies retrieval of default preferences and update operations."""
    u = await _create_test_user_with_role(db_session, f"p_{uuid.uuid4().hex[:6]}@example.com", "CONSUMER")
    token = create_access_token(subject=str(u.id), role="CONSUMER")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get default preferences
    get_resp = await client.get("/api/v1/notifications/preferences", headers=headers)
    assert get_resp.status_code == 200
    prefs = get_resp.json()
    assert prefs["expiry_alerts"] is True
    assert prefs["quiet_hours_enabled"] is False

    # 2. Update preferences
    update_resp = await client.put(
        "/api/v1/notifications/preferences",
        json={"quiet_hours_enabled": True, "quiet_hours_start": "23:00"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["quiet_hours_enabled"] is True
    assert updated["quiet_hours_start"] == "23:00"


@pytest.mark.asyncio
async def test_device_registration_and_isolation(client: AsyncClient, db_session: AsyncSession):
    """Verifies device registration, update, deletion, and cross-user isolation."""
    u1 = await _create_test_user_with_role(db_session, f"d1_{uuid.uuid4().hex[:6]}@example.com", "CONSUMER")
    h1 = {"Authorization": f"Bearer {create_access_token(subject=str(u1.id), role='CONSUMER')}"}

    u2 = await _create_test_user_with_role(db_session, f"d2_{uuid.uuid4().hex[:6]}@example.com", "CONSUMER")
    h2 = {"Authorization": f"Bearer {create_access_token(subject=str(u2.id), role='CONSUMER')}"}

    # Register device for User 1
    reg1 = await client.post(
        "/api/v1/notifications/devices",
        json={"device_id": "pixel-7-device-01", "platform": "android", "fcm_token": "fcm_sample_token_123"},
        headers=h1,
    )
    assert reg1.status_code == 201
    assert reg1.json()["device_id"] == "pixel-7-device-01"

    # User 2 attempts to delete User 1's device registration -> 404
    del2 = await client.delete("/api/v1/notifications/devices/pixel-7-device-01", headers=h2)
    assert del2.status_code == 404

    # User 1 deletes own device -> 204
    del1 = await client.delete("/api/v1/notifications/devices/pixel-7-device-01", headers=h1)
    assert del1.status_code == 204


@pytest.mark.asyncio
async def test_notification_records_and_read_status_flow(client: AsyncClient, db_session: AsyncSession):
    """Verifies notification creation, unread count, read-marking, and cross-user isolation."""
    u1 = await _create_test_user_with_role(db_session, f"n1_{uuid.uuid4().hex[:6]}@example.com", "CONSUMER")
    h1 = {"Authorization": f"Bearer {create_access_token(subject=str(u1.id), role='CONSUMER')}"}

    u2 = await _create_test_user_with_role(db_session, f"n2_{uuid.uuid4().hex[:6]}@example.com", "CONSUMER")
    h2 = {"Authorization": f"Bearer {create_access_token(subject=str(u2.id), role='CONSUMER')}"}

    # Create server notification record for User 1
    rec = await create_notification_record(
        db_session,
        user_id=u1.id,
        notification_type="EXPIRY_3_DAY",
        title="Milk Expiring Soon",
        body="Your milk expires in 3 days.",
    )

    # 1. Unread count for User 1
    uc1 = await client.get("/api/v1/notifications/unread-count", headers=h1)
    assert uc1.status_code == 200
    assert uc1.json()["unread_count"] == 1

    # 2. List notifications for User 1
    list1 = await client.get("/api/v1/notifications", headers=h1)
    assert list1.status_code == 200
    items1 = list1.json()
    assert len(items1) == 1
    assert items1[0]["title"] == "Milk Expiring Soon"

    # 3. User 2 attempts to mark User 1's notification as read -> 404
    read2 = await client.post(f"/api/v1/notifications/{rec.id}/read", headers=h2)
    assert read2.status_code == 404

    # 4. User 1 marks own notification as read -> 200
    read1 = await client.post(f"/api/v1/notifications/{rec.id}/read", headers=h1)
    assert read1.status_code == 200
    assert read1.json()["is_read"] is True

    # 5. Unread count is now 0
    uc1_after = await client.get("/api/v1/notifications/unread-count", headers=h1)
    assert uc1_after.json()["unread_count"] == 0


@pytest.mark.asyncio
async def test_firebase_admin_initialization_missing_credentials(monkeypatch):
    """Verifies missing GOOGLE_APPLICATION_CREDENTIALS safely returns None."""
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with patch("firebase_admin._apps", {}):
        app = initialize_firebase_admin()
        assert app is None


@pytest.mark.asyncio
async def test_firebase_admin_initialization_invalid_path(monkeypatch):
    """Verifies invalid file path safely returns None."""
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/does/not/exist/secrets.json")
    with patch("firebase_admin._apps", {}):
        app = initialize_firebase_admin()
        assert app is None


@pytest.mark.asyncio
async def test_select_default_fcm_provider_production_strict_error(monkeypatch):
    """Verifies missing credentials in production raises explicit RuntimeError."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    with pytest.raises(RuntimeError, match="GOOGLE_APPLICATION_CREDENTIALS"):
        select_default_fcm_provider()



@pytest.mark.asyncio
async def test_firebase_fcm_provider_dispatch_success():
    """Verifies successful dispatch using mocked firebase_admin.messaging."""
    mock_app = MagicMock()
    provider = FirebaseFCMProvider(app=mock_app)

    with patch("firebase_admin.messaging.send", return_value="projects/test/messages/msg_123"):
        result = await provider.send_push_notification(
            "valid_fcm_token_123", "Title", "Body", {"key": "value"}
        )
        assert result is True


@pytest.mark.asyncio
async def test_firebase_fcm_provider_invalid_token_handling():
    """Verifies UnregisteredError raises TokenUnregisteredError."""
    mock_app = MagicMock()
    provider = FirebaseFCMProvider(app=mock_app)

    with patch(
        "firebase_admin.messaging.send",
        side_effect=messaging.UnregisteredError("Requested entity was not found."),
    ):
        with pytest.raises(TokenUnregisteredError):
            await provider.send_push_notification("invalid_fcm_token_999", "Title", "Body")


@pytest.mark.asyncio
async def test_multi_device_dispatch_with_partial_failure(db_session: AsyncSession):
    """Verifies deactivation of invalid device token while successfully delivering to valid device."""
    u = await _create_test_user_with_role(
        db_session, f"md_{uuid.uuid4().hex[:6]}@example.com", "CONSUMER"
    )

    # Device 1: Valid
    d1 = await register_consumer_device(
        db_session, u.id, "device-1", "android", "fcm_token_valid"
    )
    # Device 2: Invalid
    d2 = await register_consumer_device(
        db_session, u.id, "device-2", "android", "fcm_token_invalid"
    )

    class MockPartialFailureProvider(FCMProvider):
        async def send_push_notification(
            self, fcm_token: str, title: str, body: str, data=None
        ) -> bool:
            if fcm_token == "fcm_token_invalid":
                raise TokenUnregisteredError(fcm_token)
            return True

    original_provider = get_fcm_provider()
    try:
        set_fcm_provider(MockPartialFailureProvider())
        record = await create_notification_record(
            db_session,
            user_id=u.id,
            notification_type="EXPIRY_TODAY",
            title="Partial Failure Test",
            body="Testing partial token failure",
        )
        assert record.status == "DELIVERED"

        # Refresh d2 to verify is_active became False
        await db_session.refresh(d2)
        assert d2.is_active is False

        # d1 should remain active
        await db_session.refresh(d1)
        assert d1.is_active is True
    finally:
        set_fcm_provider(original_provider)
