# AVENZO Production Deployment Guide

This guide outlines the step-by-step production deployment workflow for the **Avenzo Monorepo** (FastAPI Backend, PostgreSQL, Firebase Cloud Messaging, and Flutter Consumer Mobile Application).

---

## 1. System Requirements & Architecture

- **Backend:** Python 3.12 or 3.13, FastAPI, Uvicorn (or Gunicorn with Uvicorn workers)
- **Database:** PostgreSQL 16+ with `asyncpg` driver
- **Push Notifications:** Firebase Cloud Messaging (FCM) via Firebase Admin SDK
- **Containerization:** Docker & Docker Compose (optional / recommended)
- **SSL / Ingress:** Nginx / Caddy / AWS ALB / Cloudflare with HTTPS

---

## 2. Environment Variables & Secret Management

All sensitive production secrets must be supplied strictly via environment variables. **Never commit `.env` or secret files to Git.**

Copy `backend/.env.example` to `.env` on your production server:

```ini
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
APP_VERSION=0.1.0

DATABASE_URL=postgresql+asyncpg://avenzo_prod_user:SECURE_PASSWORD@prod-db-host:5432/avenzo_prod_db
DATABASE_HOST=prod-db-host
DATABASE_PORT=5432
DATABASE_NAME=avenzo_prod_db
DATABASE_USER=avenzo_prod_user
DATABASE_PASSWORD=SECURE_PASSWORD

JWT_SECRET=GENERATED_CRYPTO_RANDOM_SECRET_KEY_MIN_64_CHARACTERS
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

ALLOWED_ORIGINS=https://consumer.avenzo.app,https://business.avenzo.app
LOG_LEVEL=INFO

FCM_PROJECT_ID=avenzo-116165
GOOGLE_APPLICATION_CREDENTIALS=/path/to/external/secrets/service-account.json
```

---

## 3. Database Migration & Initialization

Run database migrations using Alembic prior to starting the production FastAPI process:

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

---

## 4. Backend Deployment (Docker / Bare Metal)

### Option A: Docker Deployment (Recommended)

Build and launch the container using the multi-stage non-root `Dockerfile`:

```bash
cd backend
docker build -t avenzo-backend:latest .
docker run -d \
  --name avenzo-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file /etc/avenzo/.env \
  -v /etc/avenzo/secrets:/app/secrets:ro \
  avenzo-backend:latest
```

### Option B: Systemd / Bare Metal

```bash
cd backend
source venv/bin/activate
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/avenzo/access.log \
  --error-logfile /var/log/avenzo/error.log
```

---

## 5. Health & Readiness Verification

After deployment, verify system health and database connectivity:

```bash
# Liveness Probe (Load Balancer / Kubernetes)
curl -s http://localhost:8000/health

# Readiness Probe (Verifies PostgreSQL connectivity)
curl -s http://localhost:8000/readiness
```

Expected readiness output:
```json
{
  "service": "avenzo-backend",
  "status": "ready",
  "dependencies": {
    "database": "healthy",
    "fcm": "configured"
  }
}
```

---

## 6. Flutter Mobile App Release Build

Build the production Flutter Android APK with the production backend API URL:

```bash
cd consumer-app
flutter build apk --release \
  --dart-define=API_BASE_URL=https://api.avenzo.app
```

The compiled release APK will be generated at:
`consumer-app/build/app/outputs/flutter-apk/app-release.apk`
