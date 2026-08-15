# AVENZO AI Service

> AI/ML Microservice for the AVENZO Platform
> **Foundation Scaffold — Phase 0**

---

## Overview

This service provides AI/ML capabilities for the AVENZO platform, including:

- **Demand Forecasting** — Predict future product demand
- **Stockout Prediction** — Identify risk of running out of stock
- **Waste Prediction** — Predict likely product waste (expiry)
- **Expiry Risk Scoring** — Score inventory batches by expiry risk
- **OCR Pipeline** — Extract product/batch/date info from images

> ⚠️ **AI Principle**: All outputs are advisory only. No AI model modifies authoritative database records. Human or system approval is required for all AI-recommended actions.

---

## Current Status

This is a **foundation scaffold**. No AI models are implemented yet.

- ✅ Service structure created
- ✅ `/health` endpoint available
- ❌ No models loaded
- ❌ No prediction endpoints (Phase 4)

---

## Setup

```bash
cd ai-service

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start service
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Service available at: http://localhost:8001
Health check: http://localhost:8001/health
API docs: http://localhost:8001/docs

---

## Architecture

```
ai-service/
├── app/
│   ├── main.py          FastAPI entry point
│   ├── models/          ML model wrappers
│   ├── services/        Prediction services (one per model type)
│   ├── pipelines/       Data preprocessing pipelines
│   └── utils/           Utility functions
├── models/              Trained model artifacts (gitignored)
├── notebooks/           Jupyter notebooks for exploration
├── tests/               pytest tests
└── requirements.txt     Python dependencies
```

---

## Communication

The AI service is an **internal microservice** — it is not exposed publicly.

Only the FastAPI backend communicates with the AI service:
```
Client → Backend API → AI Service → Prediction → Backend → Client
```

---

*AVENZO AI Service — Phase 0 Foundation*
