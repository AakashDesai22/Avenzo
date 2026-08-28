#!/bin/sh
set -e

echo "[AVENZO PRODUCTION BOOTSTRAP] Running safe Alembic database baseline detection and migrations..."
python -m app.core.migration_bootstrap

echo "[AVENZO PRODUCTION BOOTSTRAP] Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
