# AVENZO — System Architecture

> Document Status: **DRAFT — Foundation Phase**
> Last Updated: 2026-08-15
> Author: Architecture Team

---

## 1. Overview

AVENZO is a product lifecycle intelligence platform with three primary user-facing layers:

1. **Consumer Mobile Application** — Flutter (Android / iOS)
2. **Business Web Application** — React + TypeScript
3. **Backend API** — Python + FastAPI

These layers communicate exclusively through a REST API. No client directly accesses the database.

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     AVENZO PLATFORM                     │
├─────────────────────────┬───────────────────────────────┤
│   Consumer Mobile App   │    Business Web Application   │
│   Flutter + Dart        │    React + TypeScript (Vite)  │
│   Android / iOS         │    Browser-based              │
└────────────┬────────────┴────────────┬──────────────────┘
             │                         │
             └────────────┬────────────┘
                          │
                   REST API (HTTPS)
                   JSON payloads
                   JWT Authentication
                          │
              ┌───────────▼───────────┐
              │   FastAPI Backend     │
              │   Python 3.13+        │
              │   Uvicorn / Gunicorn  │
              └───┬───────┬───────┬───┘
                  │       │       │
         ┌────────▼─┐  ┌──▼──┐  ┌▼────────────┐
         │PostgreSQL│  │ AI  │  │  Firebase   │
         │Database  │  │Svc  │  │   FCM       │
         └──────────┘  └─────┘  └─────────────┘
```

---

## 3. Frontend Architecture

### 3.1 Consumer Mobile App (Flutter)

**Technology:** Flutter 3.x + Dart

**Architecture Pattern:** Feature-First with Riverpod state management

```
consumer-app/lib/
├── main.dart                    Entry point
├── app/
│   └── app.dart                 Root widget, routing, theme
├── core/
│   ├── constants/               App-wide constants
│   ├── services/
│   │   └── api_service.dart     HTTP client wrapper
│   ├── utils/                   Utility functions
│   └── errors/                  Error handling
├── features/
│   ├── auth/                    Login, registration
│   ├── products/                Product browsing
│   ├── cart/                    Shopping cart
│   ├── orders/                  Order history
│   ├── pantry/                  Digital pantry
│   └── notifications/           Push notifications
└── shared/
    ├── widgets/                 Shared UI components
    └── models/                  Shared data models
```

**State Management:** Riverpod (flutter_riverpod)
- Providers for each feature domain
- AsyncNotifiers for async operations
- ConsumerWidget for reactive UI
- No mixing of state management libraries

**API Communication:**
- All HTTP calls go through `core/services/api_service.dart`
- Base URL loaded from environment configuration
- JWT token attached automatically to authenticated requests
- Response error handling centralized

### 3.2 Business Web Application (React + TypeScript)

**Technology:** React 18 + TypeScript + Vite

**Architecture Pattern:** Feature-based folder structure

```
business-web/src/
├── api/
│   ├── client.ts                Axios/fetch configuration
│   ├── auth.api.ts              Auth API calls
│   ├── inventory.api.ts         Inventory API calls
│   └── ...                     (one file per domain)
├── components/
│   ├── common/                  Reusable generic components
│   ├── layout/                  Layout components
│   └── ...
├── pages/
│   ├── Dashboard.tsx
│   ├── Inventory/
│   └── ...
├── hooks/                       Custom React hooks
├── types/                       TypeScript interfaces
├── utils/                       Pure utility functions
├── context/                     React context providers (auth, theme)
└── App.tsx                      Root component, router
```

**Key Principles:**
- Strict TypeScript — `any` type not permitted
- API calls only through `src/api/` layer
- Environment variables via `import.meta.env`
- No hardcoded API URLs anywhere in source code

---

## 4. Backend Architecture

**Technology:** Python 3.13 + FastAPI

**Architecture Pattern:** Layered — API → Service → Repository → Database

```
backend/app/
├── main.py                      FastAPI application factory
├── core/
│   ├── config.py                Settings from environment (Pydantic)
│   ├── security.py              JWT creation/verification
│   ├── database.py              SQLAlchemy engine/session
│   └── dependencies.py         FastAPI dependency injections
├── api/
│   └── v1/
│       ├── health.py            GET /health
│       ├── auth.py              POST /auth/*
│       ├── users.py             CRUD /users/*
│       └── ...                  (one router per domain)
├── models/                      SQLAlchemy ORM models
├── schemas/                     Pydantic request/response schemas
├── services/                    Business logic (pure Python)
├── repositories/                Database access (SQLAlchemy queries)
├── middleware/                  CORS, logging, error middleware
└── utils/                       Shared utilities
```

**Layer Responsibilities:**

| Layer | Responsibility |
|-------|---------------|
| `api/` | HTTP routing, request validation, response formatting |
| `services/` | Business logic, validation rules, orchestration |
| `repositories/` | Database queries, ORM operations |
| `models/` | SQLAlchemy table definitions |
| `schemas/` | Pydantic validation — request and response bodies |

**API Versioning:**
- All endpoints prefixed with `/api/v1/`
- Version is in the URL path
- Future versions will use `/api/v2/` etc.

---

## 5. Database Architecture

**Technology:** PostgreSQL 15+

**ORM:** SQLAlchemy (async)
**Migrations:** Alembic

**Core Design Principles:**
- Every table has a UUID primary key
- Every table has `created_at` and `updated_at` timestamps
- Soft delete pattern via `is_deleted` and `deleted_at` fields where appropriate
- Foreign key constraints enforced at database level
- Status fields use string enums (validated in application layer)

See [../database/schema.md](../database/schema.md) for full entity design.

---

## 6. AI/ML Service Architecture

**Technology:** Python + FastAPI + scikit-learn + Pandas + NumPy

**Design:** Separate microservice communicating with the backend via internal REST API

```
ai-service/app/
├── main.py                      AI service FastAPI entry
├── models/                      ML model class wrappers
├── services/                    Prediction services
├── pipelines/                   Data preprocessing pipelines
└── utils/                       Helpers
```

**AI Communication Flow:**
```
Backend → (internal API call) → AI Service → Model → Prediction → Backend → Client
```

**AI Safety Principle:**
- AI outputs are ADVISORY only
- AI predictions are stored as recommendations
- A business user or system must explicitly approve AI-driven actions
- AI service NEVER directly writes to the main database
- All AI interactions are logged for audit purposes

**Planned Models:**
| Model | Type | Library |
|-------|------|---------|
| Demand Forecasting | Time series | scikit-learn / statsmodels |
| Stockout Prediction | Classification | scikit-learn |
| Waste Prediction | Regression | scikit-learn |
| Expiry Risk Score | Scoring | Custom logic + ML |
| OCR Pipeline | Computer vision | TBD (lightweight open-source) |

---

## 7. Notification Architecture

**Technology:** Firebase Cloud Messaging (FCM)

**Flow:**
```
Event (e.g. product expiring) → Backend detects → FCM Service → Push to Device
```

**Notification Types:**
- Consumer: Pantry item expiry warnings
- Consumer: Order status updates
- Business: Low stock alerts
- Business: Expiry risk alerts

**Implementation:** Backend calls FCM HTTP API using the server SDK. Consumer app registers FCM token on login. Token stored per user in the database.

---

## 8. Authentication Architecture

**Technology:** JWT (JSON Web Tokens)

**Flow:**
```
Client → POST /api/v1/auth/login → Backend validates credentials
      ← Returns: { access_token, refresh_token }
Client → Subsequent requests include: Authorization: Bearer <access_token>
Backend → Validates token signature + expiry → Extracts user identity + role
```

**Token Configuration:**
- Access token: short-lived (default 30 minutes)
- Refresh token: longer-lived (7 days)
- Algorithm: HS256
- Roles: Admin, Manager, Staff, Consumer

**Role-Based Access Control (RBAC):**
- Each API endpoint declares required roles
- Backend enforces roles via FastAPI dependencies
- Frontend adjusts UI visibility based on role (but backend always enforces)

---

## 9. API Communication Standards

- **Protocol:** HTTPS (HTTP in development)
- **Format:** JSON
- **Versioning:** URL path versioning (`/api/v1/`)
- **Authentication:** Bearer token in `Authorization` header
- **Error format:** Standardized JSON error envelope
- **Pagination:** Cursor or offset-based, configured per endpoint

See [../api/api-design.md](../api/api-design.md) for full API specification.

---

## 10. Critical Architectural Principles

> **NEVER:** Frontend → Database directly
> **ALWAYS:** Frontend → REST API → Backend → Database

> **NEVER:** AI silently modifies critical inventory records
> **ALWAYS:** AI recommendations require human or system approval

> **NEVER:** Credentials or secrets in source code
> **ALWAYS:** Environment variables, never committed to Git

> **NEVER:** Business logic in the frontend
> **ALWAYS:** Business logic in the backend service layer

---

## 11. External Services Summary

| Service | Purpose | Status |
|---------|---------|--------|
| PostgreSQL | Primary database | Planned |
| Firebase FCM | Push notifications | Planned |
| Object Storage | Media/image storage | Planned (TBD provider) |
| Redis | Caching / task queues | Future consideration |

---

## 12. Development Environment

See [../development/DEVELOPMENT_GUIDE.md](../development/DEVELOPMENT_GUIDE.md) for local development setup.

Development stack uses Docker Compose to run PostgreSQL locally alongside the FastAPI backend.

---

*Architecture Document — AVENZO Phase 0 Foundation*
