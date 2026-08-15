# AVENZO — Database

This directory contains database design documents, migrations, and seed data.

## Contents

| Directory | Purpose |
|-----------|---------|
| `schema/` | Schema design documentation |
| `migrations/` | Alembic migration files (Phase 1+) |
| `seeds/` | Seed data scripts for development |

## Status

| Component | Status |
|-----------|--------|
| Schema Design | ✅ Documented (see docs/database/schema.md) |
| Migrations | ❌ Not created (Phase 1) |
| Seed Data | ❌ Not created (Phase 1) |
| Alembic Setup | ❌ Not configured (Phase 1) |

## Usage (Phase 1+)

```bash
# Navigate to backend (Alembic runs from there)
cd backend

# Create a new migration
alembic revision --autogenerate -m "your migration description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

## Schema Overview

See [../docs/database/schema.md](../docs/database/schema.md) for the complete entity design.

## PostgreSQL Setup

For local development, use Docker Compose:

```bash
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres
```
