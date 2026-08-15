"""
AVENZO Backend — Application Entry Point
FastAPI application factory and startup configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.api.v1.health import router as health_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        f"Starting AVENZO Backend v{settings.APP_VERSION} "
        f"in {settings.APP_ENV} mode"
    )
    yield
    # Shutdown
    logger.info("AVENZO Backend shutting down")


def create_app() -> FastAPI:
    """
    Application factory function.
    Creates and configures the FastAPI application instance.
    """
    app = FastAPI(
        title="AVENZO API",
        description=(
            "AI-Driven Product Lifecycle Intelligence Platform. "
            "One Product. One Lifecycle. One Intelligence."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(health_router)

    return app


# Create the application instance
app = create_app()


@app.get("/health", tags=["Health"], summary="Basic Health Check")
async def root_health_check() -> dict:
    """
    Root-level health check endpoint.
    Used by load balancers and uptime monitors.
    Returns a simple healthy status.
    """
    return {
        "service": "avenzo-backend",
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
