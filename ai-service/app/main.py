"""
AVENZO AI Service — Entry Point
FastAPI service for AI/ML predictions and recommendations.

NOTE: This is a foundation scaffold only.
AI models and full implementation begin in Phase 4.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

AI_SERVICE_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup and shutdown."""
    logger.info(f"Starting AVENZO AI Service v{AI_SERVICE_VERSION}")
    yield
    logger.info("AVENZO AI Service shutting down")


app = FastAPI(
    title="AVENZO AI Service",
    description=(
        "AI/ML Microservice for AVENZO Platform. "
        "Provides demand forecasting, expiry risk, stockout predictions, "
        "waste predictions, and smart recommendations. "
        "AI outputs are advisory only — not authoritative records."
    ),
    version=AI_SERVICE_VERSION,
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Backend only — not public
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"], summary="AI Service Health Check")
async def health_check() -> dict:
    """
    Health check endpoint for the AVENZO AI Service.
    
    Returns service status, version, and loaded models.
    Models are not loaded in Phase 0 (foundation only).
    """
    return {
        "service": "avenzo-ai-service",
        "status": "healthy",
        "version": AI_SERVICE_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models_loaded": {
            "demand_forecasting": False,     # Phase 4
            "stockout_prediction": False,    # Phase 4
            "waste_prediction": False,       # Phase 4
            "expiry_risk_scoring": False,    # Phase 4
            "ocr_pipeline": False,           # Phase 4
        },
        "note": "AI models not yet trained or loaded. Foundation scaffold only.",
    }
