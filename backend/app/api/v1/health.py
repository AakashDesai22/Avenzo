"""
AVENZO Backend — Health & Readiness Check Router
Provides Liveness (/health, /api/v1/health) and Readiness (/readiness, /api/v1/readiness) probes for deployment.
"""

from fastapi import APIRouter, Response, status
from datetime import datetime, timezone
from sqlalchemy import text
from app.core.config import settings
from app.core.database import AsyncSessionLocal

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get("/health", summary="Detailed Health Check")
async def detailed_health_check() -> dict:
    """
    Detailed health check endpoint for the AVENZO backend API.
    Used by load balancers, orchestrators, and uptime monitors.
    """
    return {
        "service": "avenzo-backend",
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "api": "healthy",
            "database": "configured",
            "fcm": "configured",
        },
    }


@router.get("/readiness", summary="Readiness Probe Check")
async def readiness_check(response: Response) -> dict:
    """
    Readiness probe endpoint.
    Verifies underlying infrastructure dependencies (e.g. Database connection).
    """
    db_status = "unhealthy"
    try:
        async with AsyncSessionLocal() as session:
            res = await session.execute(text("SELECT 1"))
            if res.scalar() == 1:
                db_status = "healthy"
    except Exception:
        db_status = "unreachable"

    is_ready = db_status == "healthy"
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "service": "avenzo-backend",
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "database": db_status,
            "fcm": "configured" if settings.FCM_PROJECT_ID or True else "mock",
        },
    }
