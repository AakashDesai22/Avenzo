"""
AVENZO Backend — Test Suite: Automated Expiry Monitoring Service & Internal Endpoint
Tests for expiry monitoring cycles, DTE thresholds, deduplication, preferences, FCM handling, and endpoint security.
"""

import pytest
import pytest_asyncio
import uuid
import json
from datetime import timedelta
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch

from sqlalchemy import delete
from app.main import app
from app.core.config import Settings, settings
from app.core.date_utils import get_business_date
from app.models.user import User, Role
from app.models.pantry import ConsumerPantry, PantryItem
from app.models.notification import NotificationRecord, ConsumerDevice, NotificationPreference
from app.services.expiry_monitoring_service import run_expiry_monitoring_cycle
from app.services.notification_service import (
    MockFCMProvider,
    set_fcm_provider,
    get_fcm_provider,
    TokenUnregisteredError,
)


@pytest.fixture(autouse=True)
def use_mock_fcm_provider():
    """Ensure MockFCMProvider is used for all expiry monitoring tests."""
    original_provider = get_fcm_provider()
    set_fcm_provider(MockFCMProvider())
    yield
    set_fcm_provider(original_provider)


@pytest_asyncio.fixture(autouse=True)
async def clear_test_pantry_and_notifications(db_session):
    """Resets pantry items, notification records, devices, and preferences before each test."""
    await db_session.execute(delete(PantryItem))
    await db_session.execute(delete(NotificationRecord))
    await db_session.execute(delete(ConsumerDevice))
    await db_session.execute(delete(NotificationPreference))
    await db_session.commit()



async def _setup_test_user_and_pantry(db_session, email_prefix: str) -> tuple[User, ConsumerPantry]:
    """Helper fixture to create a consumer user and pantry."""
    unique_email = f"{email_prefix}_{uuid.uuid4().hex[:6]}@avenzo.dev"
    role_res = await db_session.execute(
        NotificationRecord.__table__.select().where(False)  # Dummy query to ensure db connection
    )
    
    # Create or fetch Consumer role
    from sqlalchemy.future import select
    res = await db_session.execute(select(Role).where(Role.name == "CONSUMER"))
    role = res.scalars().first()
    if not role:
        role = Role(name="CONSUMER", description="Consumer role")
        db_session.add(role)
        await db_session.flush()

    user = User(
        email=unique_email,
        password_hash="hashed_pw",
        first_name="Pantry",
        last_name="Tester",
        role_id=role.id,
        user_type="consumer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    pantry = ConsumerPantry(
        user_id=user.id,
        name="Test Home Pantry",
        is_default=True,
    )
    db_session.add(pantry)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(pantry)
    return user, pantry


@pytest.mark.asyncio
async def test_expiry_monitoring_no_expiring_products(db_session):
    """Scenario A: Test cycle with no active expiring pantry items."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "no_exp")

    # Item with no expiry date
    item = PantryItem(
        pantry_id=pantry.id,
        custom_name="Non-expiring Salt",
        quantity=1.0,
        expiry_date=None,
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    summary = await run_expiry_monitoring_cycle(db_session)
    assert summary["status"] == "completed"
    assert summary["notifications_created"] == 0


@pytest.mark.asyncio
async def test_expiry_monitoring_7_days_away(db_session):
    """Scenario B: Product exactly 7 days away generates EXPIRY_7_DAY."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "exp_7")
    today = get_business_date()

    item = PantryItem(
        pantry_id=pantry.id,
        custom_name="Milk 7d",
        quantity=1.0,
        expiry_date=today + timedelta(days=7),
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    summary = await run_expiry_monitoring_cycle(db_session)
    assert summary["notifications_created"] == 1

    from sqlalchemy.future import select
    res = await db_session.execute(
        select(NotificationRecord).where(NotificationRecord.user_id == user.id)
    )
    records = list(res.scalars().all())
    assert len(records) == 1
    assert records[0].notification_type == "EXPIRY_7_DAY"
    assert "Milk 7d" in records[0].body


@pytest.mark.asyncio
async def test_expiry_monitoring_3_days_away(db_session):
    """Scenario C: Product exactly 3 days away generates EXPIRY_3_DAY."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "exp_3")
    today = get_business_date()

    item = PantryItem(
        pantry_id=pantry.id,
        custom_name="Yogurt 3d",
        quantity=2.0,
        expiry_date=today + timedelta(days=3),
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    summary = await run_expiry_monitoring_cycle(db_session)
    assert summary["notifications_created"] == 1

    from sqlalchemy.future import select
    res = await db_session.execute(
        select(NotificationRecord).where(NotificationRecord.user_id == user.id)
    )
    records = list(res.scalars().all())
    assert len(records) == 1
    assert records[0].notification_type == "EXPIRY_3_DAY"


@pytest.mark.asyncio
async def test_expiry_monitoring_expiring_today(db_session):
    """Scenario D: Product expiring today generates EXPIRY_TODAY."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "exp_0")
    today = get_business_date()

    item = PantryItem(
        pantry_id=pantry.id,
        custom_name="Fresh Bread Today",
        quantity=1.0,
        expiry_date=today,
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    summary = await run_expiry_monitoring_cycle(db_session)
    assert summary["notifications_created"] == 1

    from sqlalchemy.future import select
    res = await db_session.execute(
        select(NotificationRecord).where(NotificationRecord.user_id == user.id)
    )
    records = list(res.scalars().all())
    assert len(records) == 1
    assert records[0].notification_type == "EXPIRY_TODAY"


@pytest.mark.asyncio
async def test_expiry_monitoring_already_expired(db_session):
    """Scenario E: Already expired product generates PRODUCT_EXPIRED."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "exp_old")
    today = get_business_date()

    item = PantryItem(
        pantry_id=pantry.id,
        custom_name="Old Cheese",
        quantity=1.0,
        expiry_date=today - timedelta(days=2),
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    summary = await run_expiry_monitoring_cycle(db_session)
    assert summary["notifications_created"] == 1

    from sqlalchemy.future import select
    res = await db_session.execute(
        select(NotificationRecord).where(NotificationRecord.user_id == user.id)
    )
    records = list(res.scalars().all())
    assert len(records) == 1
    assert records[0].notification_type == "PRODUCT_EXPIRED"


@pytest.mark.asyncio
async def test_expiry_monitoring_multiple_products(db_session):
    """Scenario F: Multiple items with various DTE values process in a single cycle."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "exp_multi")
    today = get_business_date()

    item7 = PantryItem(pantry_id=pantry.id, custom_name="Item 7d", expiry_date=today + timedelta(days=7), status="active")
    item3 = PantryItem(pantry_id=pantry.id, custom_name="Item 3d", expiry_date=today + timedelta(days=3), status="active")
    item0 = PantryItem(pantry_id=pantry.id, custom_name="Item Today", expiry_date=today, status="active")
    item_safe = PantryItem(pantry_id=pantry.id, custom_name="Item Safe 10d", expiry_date=today + timedelta(days=10), status="active")

    db_session.add_all([item7, item3, item0, item_safe])
    await db_session.commit()

    summary = await run_expiry_monitoring_cycle(db_session)
    assert summary["notifications_created"] == 3
    assert summary["notifications_suppressed"] == 0


@pytest.mark.asyncio
async def test_expiry_monitoring_duplicate_suppression(db_session):
    """Scenario G: Running cycle twice suppresses duplicate notifications."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "dup_test")
    today = get_business_date()

    item = PantryItem(
        pantry_id=pantry.id,
        custom_name="Dup Cheese",
        expiry_date=today + timedelta(days=3),
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    # First run: creates notification
    sum1 = await run_expiry_monitoring_cycle(db_session)
    assert sum1["notifications_created"] == 1
    assert sum1["notifications_suppressed"] == 0

    # Second run: suppresses duplicate
    sum2 = await run_expiry_monitoring_cycle(db_session)
    assert sum2["notifications_created"] == 0
    assert sum2["notifications_suppressed"] == 1


@pytest.mark.asyncio
async def test_expiry_monitoring_preference_disabled(db_session):
    """Scenario H: When notification preferences are disabled, FCM push dispatch is skipped."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "pref_dis")
    today = get_business_date()

    # Set user preference expiry_alerts = False
    pref = NotificationPreference(
        user_id=user.id,
        expiry_alerts=False,
        critical_expiry_alerts=False,
    )
    db_session.add(pref)

    # Register active device
    device = ConsumerDevice(
        user_id=user.id,
        device_id="test_device_pref",
        platform="android",
        fcm_token="fcm_token_pref_disabled",
        is_active=True,
    )
    db_session.add(device)

    item = PantryItem(
        pantry_id=pantry.id,
        custom_name="Pref Disabled Butter",
        expiry_date=today + timedelta(days=7),
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    summary = await run_expiry_monitoring_cycle(db_session)
    assert summary["notifications_created"] == 1
    assert summary["notifications_sent"] == 0  # Push skipped!

    from sqlalchemy.future import select
    res = await db_session.execute(
        select(NotificationRecord).where(NotificationRecord.user_id == user.id)
    )
    rec = res.scalars().first()
    assert rec.status == "CREATED"  # Saved in DB, but not sent over FCM


@pytest.mark.asyncio
async def test_expiry_monitoring_one_failure_continues(db_session):
    """Scenario I: One notification failure does not terminate the cycle for other items."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "err_cont")
    today = get_business_date()

    item1 = PantryItem(pantry_id=pantry.id, custom_name="Item 1", expiry_date=today + timedelta(days=7), status="active")
    item2 = PantryItem(pantry_id=pantry.id, custom_name="Item 2", expiry_date=today + timedelta(days=3), status="active")
    db_session.add_all([item1, item2])
    await db_session.commit()

    # Mock create_notification_record to fail on item1 but succeed on item2
    from app.services.expiry_monitoring_service import create_notification_record as original_create

    call_count = 0
    async def mock_create(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Simulated DB/FCM error for item 1")
        return await original_create(*args, **kwargs)

    with patch("app.services.expiry_monitoring_service.create_notification_record", side_effect=mock_create):
        summary = await run_expiry_monitoring_cycle(db_session)

    assert summary["errors"] == 1
    assert summary["notifications_created"] == 1  # Item 2 succeeded!


@pytest.mark.asyncio
async def test_expiry_monitoring_invalid_fcm_token_deactivates_device(db_session):
    """Scenario J: TokenUnregisteredError deactivates the device."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "invalid_tok")
    today = get_business_date()

    device = ConsumerDevice(
        user_id=user.id,
        device_id="dev_invalid_123",
        platform="android",
        fcm_token="bad_fcm_token_unregistered",
        is_active=True,
    )
    db_session.add(device)

    item = PantryItem(
        pantry_id=pantry.id,
        custom_name="Token Test Item",
        expiry_date=today,
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    class FailingFCMProvider(MockFCMProvider):
        async def send_push_notification(self, fcm_token: str, title: str, body: str, data=None) -> bool:
            raise TokenUnregisteredError(fcm_token)

    set_fcm_provider(FailingFCMProvider())

    summary = await run_expiry_monitoring_cycle(db_session)
    assert summary["notifications_created"] == 1

    await db_session.refresh(device)
    assert device.is_active is False  # Device deactivated!


@pytest.mark.asyncio
async def test_internal_endpoint_unauthorized(client: AsyncClient):
    """Scenario K: POST with invalid secret header returns HTTP 401."""
    response = await client.post(
        "/api/v1/internal/expiry-monitor/run",
        headers={"X-Expiry-Monitor-Secret": "wrong_secret_key"},
    )
    assert response.status_code == 401
    assert "Invalid or missing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_internal_endpoint_missing_secret_header(client: AsyncClient):
    """Scenario L: POST without secret header returns HTTP 401."""
    response = await client.post("/api/v1/internal/expiry-monitor/run")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_internal_endpoint_correct_secret(client: AsyncClient):
    """Scenario M: POST with valid secret header returns HTTP 200 with summary."""
    response = await client.post(
        "/api/v1/internal/expiry-monitor/run",
        headers={"X-Expiry-Monitor-Secret": settings.EXPIRY_MONITOR_SECRET},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "processed_items" in data
    assert "notifications_created" in data
    assert "notifications_suppressed" in data


def test_production_config_requires_strong_expiry_secret():
    """Scenario N: Production config validation requires strong EXPIRY_MONITOR_SECRET."""
    # Test dev default secret in production mode -> must raise ValueError
    with pytest.raises(ValueError, match="EXPIRY_MONITOR_SECRET must be configured"):
        Settings(
            APP_ENV="production",
            APP_DEBUG=False,
            JWT_SECRET="a_very_strong_production_jwt_secret_32chars_long",
            EXPIRY_MONITOR_SECRET="dev-only-change-me",
        )

    # Test valid strong secret in production mode -> passes validation
    prod_settings = Settings(
        APP_ENV="production",
        APP_DEBUG=False,
        JWT_SECRET="a_very_strong_production_jwt_secret_32chars_long",
        EXPIRY_MONITOR_SECRET="prod_super_secret_expiry_key_998877",
    )
    assert prod_settings.EXPIRY_MONITOR_SECRET == "prod_super_secret_expiry_key_998877"


@pytest.mark.asyncio
async def test_internal_endpoint_idempotency(client: AsyncClient, db_session):
    """Scenario O: Endpoint idempotency — running twice creates zero duplicates."""
    user, pantry = await _setup_test_user_and_pantry(db_session, "endpoint_idem")
    today = get_business_date()

    item = PantryItem(
        pantry_id=pantry.id,
        custom_name="Idempotency Milk",
        expiry_date=today + timedelta(days=7),
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    headers = {"X-Expiry-Monitor-Secret": settings.EXPIRY_MONITOR_SECRET}

    # First call
    res1 = await client.post("/api/v1/internal/expiry-monitor/run", headers=headers)
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["notifications_created"] >= 1

    # Second call
    res2 = await client.post("/api/v1/internal/expiry-monitor/run", headers=headers)
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["notifications_created"] == 0
    assert d2["notifications_suppressed"] >= 1
