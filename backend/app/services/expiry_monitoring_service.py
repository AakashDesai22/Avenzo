"""
AVENZO Backend — Automated Expiry Monitoring Service
Service performing on-demand expiry evaluation cycles for consumer pantry items.
Calculates DTE, applies notification thresholds, prevents duplicate alerts, and dispatches via FCM.
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.models.pantry import PantryItem
from app.models.notification import NotificationRecord
from app.services.expiry_service import calculate_dte
from app.services.notification_service import create_notification_record

logger = logging.getLogger(__name__)


async def run_expiry_monitoring_cycle(
    session: AsyncSession, target_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Executes a single expiry monitoring cycle over all active consumer pantry items.
    
    Thresholds evaluated:
    - DTE == 7  -> EXPIRY_7_DAY
    - DTE == 3  -> EXPIRY_3_DAY
    - DTE == 0  -> EXPIRY_TODAY
    - DTE < 0   -> PRODUCT_EXPIRED

    Returns a production-safe sanitized execution summary.
    """
    logger.info("[Expiry Monitoring] Starting expiry monitoring cycle...")

    processed_items = 0
    notifications_created = 0
    notifications_sent = 0
    notifications_suppressed = 0
    errors = 0

    # Query all active, non-deleted pantry items with an expiry date
    stmt = (
        select(PantryItem)
        .options(joinedload(PantryItem.pantry), joinedload(PantryItem.product))
        .where(
            PantryItem.status == "active",
            PantryItem.is_deleted == False,
            PantryItem.expiry_date != None,
        )
    )
    res = await session.execute(stmt)
    items = list(res.scalars().unique().all())

    for item in items:
        processed_items += 1

        if not item.pantry or not item.pantry.user_id:
            logger.warning(f"[Expiry Monitoring] Pantry item {item.id} lacks valid pantry/user association. Skipping.")
            continue

        user_id = item.pantry.user_id
        dte = calculate_dte(item.expiry_date, target_date=target_date)

        if dte is None:
            continue

        # Classify notification threshold
        if dte == 7:
            notification_type = "EXPIRY_7_DAY"
            title = "Expiry Alert: 7 Days Remaining"
        elif dte == 3:
            notification_type = "EXPIRY_3_DAY"
            title = "Expiry Alert: 3 Days Remaining"
        elif dte == 0:
            notification_type = "EXPIRY_TODAY"
            title = "Expiry Alert: Expiring Today"
        elif dte < 0:
            notification_type = "PRODUCT_EXPIRED"
            title = "Expiry Alert: Product Expired"
        else:
            # Other DTE values require no alert
            continue

        item_id_str = str(item.id)
        item_name = item.custom_name or (item.product.name if item.product else "Pantry item")

        if dte < 0:
            body = f"'{item_name}' expired on {item.expiry_date}. Please check your pantry."
        elif dte == 0:
            body = f"'{item_name}' expires today ({item.expiry_date})! Please use or consume it."
        else:
            body = f"'{item_name}' will expire in {dte} days (on {item.expiry_date})."

        # Duplicate prevention check
        dup_stmt = select(NotificationRecord).where(
            NotificationRecord.user_id == user_id,
            NotificationRecord.notification_type == notification_type,
            NotificationRecord.payload_json.like(f'%"pantry_item_id": "{item_id_str}"%'),
        )
        dup_res = await session.execute(dup_stmt)
        if dup_res.scalars().first():
            notifications_suppressed += 1
            logger.info(
                f"[Expiry Monitoring] Notification suppressed (duplicate): type={notification_type}, user_id={user_id}, item_id={item_id_str}"
            )
            continue

        # Create and dispatch notification
        try:
            payload = {
                "pantry_item_id": item_id_str,
                "product_id": str(item.product_id) if item.product_id else None,
                "expiry_date": str(item.expiry_date),
                "dte": dte,
            }
            payload_json = json.dumps(payload)

            record = await create_notification_record(
                session=session,
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                payload_json=payload_json,
            )
            notifications_created += 1
            if record.status in ("SENT", "DELIVERED"):
                notifications_sent += 1

            logger.info(
                f"[Expiry Monitoring] Notification generated: type={notification_type}, user_id={user_id}, item_id={item_id_str}, status={record.status}"
            )
        except Exception as e:
            errors += 1
            logger.error(
                f"[Expiry Monitoring Error] Dispatch failure for item {item_id_str}: {type(e).__name__}: {e}"
            )

    logger.info(
        f"[Expiry Monitoring] Cycle completed. processed={processed_items}, created={notifications_created}, sent={notifications_sent}, suppressed={notifications_suppressed}, errors={errors}"
    )

    return {
        "status": "completed",
        "processed_items": processed_items,
        "notifications_created": notifications_created,
        "notifications_sent": notifications_sent,
        "notifications_suppressed": notifications_suppressed,
        "errors": errors,
    }
