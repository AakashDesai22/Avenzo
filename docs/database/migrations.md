# AVENZO — Database Migrations Guide

> Document Status: **ACTIVE — Phase 1 Configured**
> Tool: Alembic + asyncpg

---

## Migration Architecture

Alembic is configured in `backend/` to auto-discover SQLAlchemy ORM models from `app.models`.

All migrations run asynchronously against PostgreSQL via `asyncpg`.

---

## Applied Migrations

| Revision ID | Description | Created Date | Applied Status |
|-------------|-------------|--------------|----------------|
| `f8fe01bb5199` | `phase_1_initial_schema` | 2026-08-15 | ✅ **APPLIED** (`alembic upgrade head`) |

---

## Migration Commands

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Create a new migration revision after modifying ORM models
alembic revision --autogenerate -m "your_migration_description"

# Apply all pending migrations to database
alembic upgrade head

# Rollback one migration step
alembic downgrade -1
```

---

## Database Connection Configuration

Alembic reads `DATABASE_URL` dynamically from `app.core.config.settings` which loads from `.env`.

Example:
`postgresql+asyncpg://avenzo_user:devpassword123@localhost:5432/avenzo_db`
