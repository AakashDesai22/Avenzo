"""
AVENZO Backend — Recommendation & Intelligence Service Tests
"""

import pytest
import uuid
from datetime import date, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.models.product import Product, Category, Brand
from app.models.user import User, Role
from app.models.recommendation import ConsumerRecommendation
from app.core.security import create_access_token
from tests.conftest import _create_test_user_with_role


@pytest.mark.asyncio
async def test_empty_pantry_recommendations(
    client: AsyncClient, db_session: AsyncSession
):
    """Verifies that an empty pantry returns an empty recommendation list and clean summary."""
    u_empty = await _create_test_user_with_role(db_session, f"empty_{uuid.uuid4().hex[:6]}@example.com", "CONSUMER")
    t_empty = create_access_token(subject=str(u_empty.id), role="CONSUMER")
    h_empty = {"Authorization": f"Bearer {t_empty}"}

    # Fetch recommendations
    rec_resp = await client.get("/api/v1/recommendations", headers=h_empty)
    assert rec_resp.status_code == 200
    assert rec_resp.json() == []

    # Fetch summary
    sum_resp = await client.get("/api/v1/recommendations/summary", headers=h_empty)
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert summary["total_active_items"] == 0
    assert summary["expiring_3d_count"] == 0
    assert summary["has_sufficient_history"] is False


@pytest.mark.asyncio
async def test_recommendation_generation_expiring_items(
    client: AsyncClient, consumer_headers: dict, db_session: AsyncSession
):
    """Verifies recommendation generation for items expiring within 3 days."""
    # Create expiring item via pantry API
    expiry_2d = (date.today() + timedelta(days=2)).isoformat()
    await client.post(
        "/api/v1/pantry",
        json={
            "custom_name": "Organic Milk",
            "quantity": "1.0",
            "unit": "liters",
            "expiry_date": expiry_2d,
            "storage_location": "fridge",
        },
        headers=consumer_headers,
    )

    # Fetch recommendations
    rec_resp = await client.get("/api/v1/recommendations", headers=consumer_headers)
    assert rec_resp.status_code == 200
    recs = rec_resp.json()
    assert len(recs) >= 1
    milk_rec = next(r for r in recs if "Milk" in r["title"])
    assert milk_rec["recommendation_type"] == "USE_SOON"
    assert milk_rec["priority"] in ["HIGH", "CRITICAL"]
    assert "reaches expiration date" in milk_rec["reason"]


@pytest.mark.asyncio
async def test_recommendation_dismissal_and_ownership_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    """Verifies recommendation dismissal and cross-user isolation."""
    # Create Consumer User 1
    u1 = await _create_test_user_with_role(db_session, f"u1_{uuid.uuid4().hex[:6]}@example.com", "CONSUMER")
    t1 = create_access_token(subject=str(u1.id), role="CONSUMER")
    h1 = {"Authorization": f"Bearer {t1}"}

    # Create Consumer User 2
    u2 = await _create_test_user_with_role(db_session, f"u2_{uuid.uuid4().hex[:6]}@example.com", "CONSUMER")
    t2 = create_access_token(subject=str(u2.id), role="CONSUMER")
    h2 = {"Authorization": f"Bearer {t2}"}

    # User 1 adds item expiring in 1 day
    await client.post(
        "/api/v1/pantry",
        json={"custom_name": "Fresh Spinach", "quantity": "1.0", "unit": "pack", "expiry_date": (date.today() + timedelta(days=1)).isoformat()},
        headers=h1,
    )

    # User 1 gets recommendations
    r1 = await client.get("/api/v1/recommendations", headers=h1)
    recs1 = r1.json()
    assert len(recs1) >= 1
    rec1_id = recs1[0]["id"]

    # User 2 attempts to dismiss User 1's recommendation -> 404
    dis2 = await client.post(f"/api/v1/recommendations/{rec1_id}/dismiss", headers=h2)
    assert dis2.status_code == 404

    # User 1 dismisses own recommendation -> 200
    dis1 = await client.post(f"/api/v1/recommendations/{rec1_id}/dismiss", headers=h1)
    assert dis1.status_code == 200
    assert dis1.json()["is_dismissed"] is True

    # User 1 list now excludes dismissed item
    r1_after = await client.get("/api/v1/recommendations", headers=h1)
    assert not any(r["id"] == rec1_id for r in r1_after.json())
