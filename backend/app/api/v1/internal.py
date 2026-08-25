"""
AVENZO Backend — Internal Infrastructure Router
Protected internal endpoints for system automation and external schedulers.
"""

import hmac
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.expiry_monitoring_service import run_expiry_monitoring_cycle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["Internal Infrastructure"])


@router.post(
    "/expiry-monitor/run",
    summary="Run Automated Expiry Monitoring Cycle",
    response_model=Dict[str, Any],
)
async def trigger_expiry_monitoring(
    x_expiry_monitor_secret: Optional[str] = Header(None, alias="X-Expiry-Monitor-Secret"),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Protected endpoint to trigger one complete automated expiry monitoring cycle.
    
    Requires the 'X-Expiry-Monitor-Secret' request header.
    Returns a sanitized execution summary.
    """
    configured_secret = settings.EXPIRY_MONITOR_SECRET
    app_env = settings.APP_ENV.lower()

    if app_env == "production":
        if (
            not configured_secret
            or "change-me" in configured_secret.lower()
            or len(configured_secret) < 16
        ):
            logger.error("[Security Alert] EXPIRY_MONITOR_SECRET is insecure or unconfigured in production.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error.",
            )

    if (
        not x_expiry_monitor_secret
        or not configured_secret
        or not hmac.compare_digest(x_expiry_monitor_secret, configured_secret)
    ):
        logger.warning("[Security Warning] Unauthorized trigger attempt on internal expiry monitoring endpoint.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal monitoring secret.",
        )

    summary = await run_expiry_monitoring_cycle(session)
    return summary
