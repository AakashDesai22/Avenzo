"""
AVENZO Backend — Health Check Router
Provides detailed health status for the API service.
"""

from fastapi import APIRouter
from datetime import datetime, timezone
from app.core.config import settings

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get("/health", summary="Detailed Health Check")
async def detailed_health_check() -> dict:
    """
    Detailed health check endpoint for the AVENZO backend API.
    
    Returns service status, version, environment, and timestamp.
    This endpoint is unauthenticated and intended for:
    - Load balancer health probes
    - CI/CD deployment verification
    - Uptime monitoring services
    
    Returns:
        dict: Health status payload with service metadata.
    """
    return {
        "service": "avenzo-backend",
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "api": "healthy",
            "database": "not_configured",   # Will be updated in Phase 1
            "ai_service": "not_configured", # Will be updated in Phase 4
        },
    }
