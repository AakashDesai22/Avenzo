"""
AVENZO Backend — Recommendation Service & Intelligence Engine
Rule-based explainable recommendation engine for consumer digital pantry.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_

from app.models.pantry import ConsumerPantry, PantryItem, PantryItemLog
from app.models.product import Product
from app.models.recommendation import ConsumerRecommendation
from app.services.expiry_service import calculate_dte


class RecommendationEngine(ABC):
    """Abstract interface for pluggable recommendation engines (Rule-based, ML, LLM)."""

    @abstractmethod
    async def generate_recommendations(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> List[ConsumerRecommendation]:
        pass


class RuleBasedRecommendationEngine(RecommendationEngine):
    """Deterministic, explainable recommendation engine operating on actual Avenzo lifecycle data."""

    async def generate_recommendations(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> List[ConsumerRecommendation]:
        # 1. Fetch user's active pantry items with products and logs
        stmt = (
            select(PantryItem)
            .join(ConsumerPantry)
            .where(
                ConsumerPantry.user_id == user_id,
                PantryItem.status == "active",
                PantryItem.is_deleted == False,
            )
            .options(
                selectinload(PantryItem.product),
                selectinload(PantryItem.logs),
            )
        )
        result = await session.execute(stmt)
        items: List[PantryItem] = list(result.scalars().all())

        if not items:
            return []

        # 2. Fetch past discard logs for user to assess historical waste pattern
        discard_stmt = (
            select(PantryItemLog)
            .join(PantryItem)
            .join(ConsumerPantry)
            .where(
                ConsumerPantry.user_id == user_id,
                PantryItemLog.action == "DISCARDED",
            )
        )
        discard_res = await session.execute(discard_stmt)
        discard_logs: List[PantryItemLog] = list(discard_res.scalars().all())
        has_discard_history = len(discard_logs) > 0

        # 3. Generate candidate recommendations
        recommendations: List[ConsumerRecommendation] = []
        now = datetime.now(timezone.utc)
        expiring_soon_count = 0

        for item in items:
            item_name = item.custom_name or (item.product.name if item.product else "Pantry Item")
            dte = calculate_dte(item.expiry_date)

            # Rule 1: USE_SOON (DTE <= 3 days)
            if dte is not None and dte <= 3:
                expiring_soon_count += 1
                priority = "CRITICAL" if dte <= 1 else "HIGH"
                dte_str = "today" if dte <= 0 else f"in {dte} day(s)"
                
                rec = ConsumerRecommendation(
                    user_id=user_id,
                    pantry_item_id=item.id,
                    recommendation_type="USE_SOON",
                    priority=priority,
                    title=f"Use {item_name} Soon",
                    message=f"{item_name} ({item.quantity} {item.unit}) expires {dte_str}.",
                    reason=f"Item reaches expiration date ({item.expiry_date}) within 3 days.",
                    suggested_action=f"Consume or freeze {item_name} before {item.expiry_date}.",
                    metadata_json=f'{{"dte": {dte}, "quantity": {item.quantity}}}',
                )
                recommendations.append(rec)

            # Rule 2: WASTE_RISK (DTE 4-7 days with past discard history)
            elif dte is not None and dte <= 7 and has_discard_history:
                rec = ConsumerRecommendation(
                    user_id=user_id,
                    pantry_item_id=item.id,
                    recommendation_type="WASTE_RISK",
                    priority="HIGH",
                    title=f"Waste Risk Alert: {item_name}",
                    message=f"{item_name} expires in {dte} days and similar items were discarded in your past logs.",
                    reason=f"Historical audit logs indicate past item discards prior to full consumption.",
                    suggested_action=f"Plan a meal using {item_name} to prevent waste.",
                    metadata_json=f'{{"dte": {dte}, "discard_history_count": {len(discard_logs)}}}',
                )
                recommendations.append(rec)

            # Rule 3: OVERSTOCK (Quantity >= 3 with low recent consumption)
            if item.quantity >= 3.0:
                recent_consumed = sum(
                    l.quantity_change for l in item.logs if l.action == "CONSUMED"
                )
                if recent_consumed == 0:
                    rec = ConsumerRecommendation(
                        user_id=user_id,
                        pantry_item_id=item.id,
                        recommendation_type="OVERSTOCK",
                        priority="MEDIUM",
                        title=f"High Stock: {item_name}",
                        message=f"You currently have {item.quantity} {item.unit} of {item_name} with low recent consumption.",
                        reason="Current pantry quantity significantly exceeds 14-day consumption log frequency.",
                        suggested_action="Prioritize using this product before buying additional units.",
                        metadata_json=f'{{"quantity": {item.quantity}}}',
                    )
                    recommendations.append(rec)

        # Rule 5: EXPIRY_PRIORITY (Summary recommendation if >= 3 items expiring soon)
        if expiring_soon_count >= 3:
            rec = ConsumerRecommendation(
                user_id=user_id,
                pantry_item_id=None,
                recommendation_type="EXPIRY_PRIORITY",
                priority="CRITICAL",
                title=f"Urgent: {expiring_soon_count} Items Expiring Soon",
                message=f"You have {expiring_soon_count} pantry items reaching expiration within 3 days.",
                reason="Multiple items approaching end of shelf life simultaneously.",
                suggested_action="Review your expiring items list and cook a batch meal.",
                metadata_json=f'{{"expiring_count": {expiring_soon_count}}}',
            )
            recommendations.append(rec)

        return recommendations


# Engine instance
_default_engine = RuleBasedRecommendationEngine()


async def generate_and_save_recommendations(
    session: AsyncSession, user_id: uuid.UUID
) -> List[ConsumerRecommendation]:
    """Generates fresh recommendations and updates non-dismissed DB records for user."""
    new_recs = await _default_engine.generate_recommendations(session, user_id)

    # Fetch existing non-dismissed recommendations to avoid duplicate insertions
    existing_stmt = select(ConsumerRecommendation).where(
        ConsumerRecommendation.user_id == user_id,
        ConsumerRecommendation.is_dismissed == False,
    )
    existing_res = await session.execute(existing_stmt)
    existing_recs = list(existing_res.scalars().all())

    existing_keys = {
        (r.pantry_item_id, r.recommendation_type) for r in existing_recs
    }

    saved_recs: List[ConsumerRecommendation] = list(existing_recs)

    for rec in new_recs:
        key = (rec.pantry_item_id, rec.recommendation_type)
        if key not in existing_keys:
            session.add(rec)
            saved_recs.append(rec)

    await session.commit()
    return saved_recs


async def get_active_recommendations(
    session: AsyncSession, user_id: uuid.UUID
) -> List[ConsumerRecommendation]:
    """Retrieves active non-dismissed recommendations for current consumer user."""
    # First generate / refresh recommendations
    await generate_and_save_recommendations(session, user_id)

    stmt = (
        select(ConsumerRecommendation)
        .where(
            ConsumerRecommendation.user_id == user_id,
            ConsumerRecommendation.is_dismissed == False,
        )
        .order_by(ConsumerRecommendation.created_at.desc())
    )
    res = await session.execute(stmt)
    recs = list(res.scalars().all())

    # Sort in memory by priority rank
    priority_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recs.sort(key=lambda r: priority_rank.get(r.priority.upper(), 4))
    return recs


async def dismiss_recommendation(
    session: AsyncSession, recommendation_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[ConsumerRecommendation]:
    """Dismisses a recommendation enforcing user ownership isolation."""
    stmt = select(ConsumerRecommendation).where(
        ConsumerRecommendation.id == recommendation_id,
        ConsumerRecommendation.user_id == user_id,
    )
    res = await session.execute(stmt)
    rec = res.scalar_one_or_none()

    if rec:
        rec.is_dismissed = True
        await session.commit()
        await session.refresh(rec)
        return rec
    return None


async def get_consumer_summary(session: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
    """Computes aggregate consumer intelligence metrics based on actual pantry data."""
    stmt = (
        select(PantryItem)
        .join(ConsumerPantry)
        .where(
            ConsumerPantry.user_id == user_id,
            PantryItem.status == "active",
            PantryItem.is_deleted == False,
        )
        .options(selectinload(PantryItem.logs))
    )
    res = await session.execute(stmt)
    items: List[PantryItem] = list(res.scalars().all())

    total_active = len(items)
    expiring_3d = 0
    expiring_7d = 0

    for item in items:
        dte = calculate_dte(item.expiry_date)
        if dte is not None:
            if dte <= 3:
                expiring_3d += 1
            if dte <= 7:
                expiring_7d += 1

    # Fetch audit log count
    logs_stmt = (
        select(func.count(PantryItemLog.id))
        .join(PantryItem)
        .join(ConsumerPantry)
        .where(ConsumerPantry.user_id == user_id)
    )
    logs_res = await session.execute(logs_stmt)
    total_logs = logs_res.scalar() or 0

    has_history = total_logs >= 3

    return {
        "total_active_items": total_active,
        "expiring_3d_count": expiring_3d,
        "expiring_7d_count": expiring_7d,
        "estimated_waste_risk_count": expiring_7d,
        "has_sufficient_history": has_history,
        "history_status": "Active usage tracking" if has_history else "Not enough consumption history yet.",
    }
