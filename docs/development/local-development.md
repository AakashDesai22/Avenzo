# AVENZO — Local Development Guide

> Document Status: **ACTIVE — Phase 1**

---

## Quick Start (Backend + Database)

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop (with engine running)
- Git

### 2. Start PostgreSQL Database
```bash
docker compose -f infrastructure/docker/docker-compose.dev.yml up -d postgres
```

### 3. Start Backend API Server
```bash
cd backend

# Create & activate venv (if not already created)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 4. Running Backend Tests
```bash
cd backend
venv\Scripts\pytest.exe tests/ -v
```

---

## API Endpoints Overview

| Endpoint | Method | Role | Description |
|----------|--------|------|-------------|
| `/health` | GET | Public | Root health check |
| `/api/v1/health` | GET | Public | Detailed service health |
| `/api/v1/auth/register` | POST | Public | User self-registration |
| `/api/v1/auth/login` | POST | Public | User authentication & JWT issuance |
| `/api/v1/auth/me` | GET | Authenticated | Get profile of current user |
| `/api/v1/users` | GET | Admin / Manager | List all users |
| `/api/v1/categories` | GET, POST, PUT | Admin / Manager | Product category CRUD |
| `/api/v1/products` | GET, POST, PUT | Admin / Manager | Product master CRUD |
| `/api/v1/warehouses` | GET, POST, PUT | Admin / Manager / Staff | Warehouse and location CRUD |
| `/api/v1/suppliers` | GET, POST, PUT | Admin / Manager | Supplier master CRUD |
| `/api/v1/batches` | GET, POST, PUT | Admin / Manager / Staff | Product batch & expiry tracking |
| `/api/v1/inventory` | GET | Admin / Manager / Staff | Stock balance listing |
| `/api/v1/inventory/adjust` | POST | Admin / Manager / Staff | Stock level adjustment & transaction log |
| `/api/v1/inventory/transactions` | GET | Admin / Manager / Staff | Audit log stock movement history |
