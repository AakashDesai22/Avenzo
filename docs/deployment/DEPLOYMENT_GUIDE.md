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

---

## 7. Automated Expiry Monitoring & External Scheduler Trigger

Avenzo uses an externally-triggered stateless expiry monitoring architecture. To prevent server resource leaks and support sleeping free-tier web instances (e.g. Render), no persistent background scheduler runs inside FastAPI.

### Purpose
Executes a single expiry evaluation cycle over active consumer pantry items, generating DTE threshold alerts (`EXPIRY_7_DAY`, `EXPIRY_3_DAY`, `EXPIRY_TODAY`, `PRODUCT_EXPIRED`), preventing duplicate alerts, respecting user notification preferences, and dispatching FCM push notifications.

### Environment Variable Requirement
Configure `EXPIRY_MONITOR_SECRET` in server environment variables (e.g. Render Environment Variables):

```ini
EXPIRY_MONITOR_SECRET=YOUR_SECURE_STRONG_EXPIRY_MONITOR_SECRET_KEY
```

> **Security Note**: Never commit `EXPIRY_MONITOR_SECRET` to GitHub or hardcode it in source code.

### Trigger Endpoint
- **URL**: `POST /api/v1/internal/expiry-monitor/run`
- **Header**: `X-Expiry-Monitor-Secret: <YOUR_SECURE_STRONG_EXPIRY_MONITOR_SECRET_KEY>`

Example cURL call (e.g. executed by GitHub Actions cron workflow or Cloud Scheduler):

```bash
curl -X POST "https://api.avenzo.app/api/v1/internal/expiry-monitor/run" \
  -H "X-Expiry-Monitor-Secret: YOUR_SECURE_STRONG_EXPIRY_MONITOR_SECRET_KEY" \
  -H "Content-Type: application/json"
```

Expected Response (200 OK):
```json
{
  "status": "completed",
  "processed_items": 12,
  "notifications_created": 2,
  "notifications_sent": 2,
  "notifications_suppressed": 3,
  "errors": 0
}
```

---

## 8. GitHub Actions External Expiry Scheduler Setup & Operation

Avenzo employs GitHub Actions (`.github/workflows/expiry-monitor.yml`) as an external cron scheduler to invoke the Render backend's internal monitoring endpoint on a daily basis.

### Workflow Schedule
- **Automated Schedule**: `0 1 * * *` (01:00 UTC = 06:30 AM IST daily)
- **Manual Trigger**: `workflow_dispatch` enabled via GitHub Web UI and GitHub CLI.

### Required GitHub Repository Secrets
Configure the following secrets in GitHub Repository Settings -> **Settings** -> **Secrets and variables** -> **Actions**:

1. `RENDER_API_URL`: The production Render backend base URL (e.g. `https://avenzo-backend.onrender.com`). Do not include trailing slash or API endpoint paths.
2. `EXPIRY_MONITOR_SECRET`: The strong secret key matching the `EXPIRY_MONITOR_SECRET` environment variable configured in Render.

> ⚠️ **CRITICAL SECURITY REQUIREMENT**: `EXPIRY_MONITOR_SECRET` must ONLY exist in Render Environment Variables and GitHub Repository Secrets. NEVER hardcode or commit this secret to Git, workflow YAML files, source code, or logs.

### Manual Verification Procedure (`workflow_dispatch`)
To manually trigger and test the workflow:
1. Navigate to your GitHub repository on GitHub.com.
2. Click **Actions** -> **AVENZO Expiry Monitor Scheduler**.
3. Click **Run workflow** -> Select `main` branch -> Click **Run workflow**.
4. Inspect the workflow run logs. Verify that curl reports `HTTP Response Status Code: 200` and displays a sanitized execution summary.

### Secret Rotation Procedure
If `EXPIRY_MONITOR_SECRET` needs to be rotated:
1. Generate a new strong cryptographic secret key (at least 16 characters).
2. Update `EXPIRY_MONITOR_SECRET` in **Render Dashboard** -> Environment Variables.
3. Update `EXPIRY_MONITOR_SECRET` in **GitHub Repository** -> Settings -> Secrets and variables -> Actions.
4. Manually trigger the workflow via `workflow_dispatch` to verify successful authentication.


