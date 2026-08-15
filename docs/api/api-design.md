# AVENZO — API Design Specification

> Document Status: **DRAFT — Foundation Phase**
> Last Updated: 2026-08-15
> Version: v1

---

## 1. API Overview

The AVENZO REST API is the single communication channel between all client applications (business web, consumer mobile) and the backend data layer. All API endpoints are served by the FastAPI backend.

**Base URL (Development):** `http://localhost:8000`
**Base URL (Production):** `https://api.avenzo.app` *(planned — not yet deployed)*

---

## 2. API Versioning

All endpoints are prefixed with `/api/v1/`.

**Strategy:** URL path versioning
- Current version: `v1`
- Future version: `v2` (additive, non-breaking if possible)
- Breaking changes require a new version prefix

```
GET /api/v1/products          # Current version
GET /api/v2/products          # Future version (when needed)
```

Rationale: URL versioning is explicit, easy to test, proxy-friendly, and does not depend on client header management.

---

## 3. Authentication

**Method:** Bearer Token (JWT)

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

**Token endpoints:**
```
POST /api/v1/auth/login           — Obtain access + refresh token
POST /api/v1/auth/refresh         — Exchange refresh token for new access token
POST /api/v1/auth/logout          — Invalidate refresh token
POST /api/v1/auth/register        — Consumer self-registration
```

**Token Lifetime:**
- Access token: 30 minutes (configurable)
- Refresh token: 7 days (configurable)

---

## 4. Request/Response Conventions

### 4.1 Content Type
All requests with a body use `Content-Type: application/json`.

### 4.2 Response Envelope
All API responses use a consistent JSON envelope:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful",
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Product with id 'abc123' was not found",
    "details": { }
  }
}
```

### 4.3 Timestamps
All timestamps in ISO 8601 format with UTC timezone:
```
2026-08-15T13:00:00Z
```

### 4.4 IDs
All resource IDs are UUIDs (string format):
```
"id": "550e8400-e29b-41d4-a716-446655440000"
```

---

## 5. Error Response Format

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST creating a resource |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation error, malformed request |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Authenticated but insufficient role/permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Duplicate resource, constraint violation |
| 422 | Unprocessable Entity | Request body validation failed (FastAPI default) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Backend temporarily unavailable |

### Error Codes (Application-level)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400/422 | Request data failed validation |
| `INVALID_CREDENTIALS` | 401 | Wrong username or password |
| `TOKEN_EXPIRED` | 401 | JWT access token has expired |
| `TOKEN_INVALID` | 401 | JWT token signature invalid |
| `INSUFFICIENT_PERMISSIONS` | 403 | User role lacks required permission |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource does not exist |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists (e.g., duplicate email) |
| `BUSINESS_RULE_VIOLATION` | 400 | Violates business logic (e.g., batch quantity) |
| `AI_SERVICE_UNAVAILABLE` | 503 | AI microservice is not responding |
| `INTERNAL_ERROR` | 500 | Unexpected internal server error |

---

## 6. Pagination

All list endpoints support pagination.

**Request Parameters:**
```
GET /api/v1/products?page=1&per_page=20&sort_by=name&sort_order=asc
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `per_page` | integer | 20 | Items per page (max 100) |
| `sort_by` | string | `created_at` | Field to sort by |
| `sort_order` | string | `desc` | `asc` or `desc` |

**Response Meta:**
```json
"meta": {
  "page": 1,
  "per_page": 20,
  "total": 150,
  "total_pages": 8,
  "has_next": true,
  "has_prev": false
}
```

---

## 7. Filtering and Search

List endpoints support filtering via query parameters:

```
GET /api/v1/products?category_id=<uuid>&is_active=true&search=milk
GET /api/v1/inventory?warehouse_id=<uuid>&expiry_before=2026-12-31
GET /api/v1/batches?status=active&supplier_id=<uuid>
```

**Search:** Full-text search on relevant fields via `search=<term>`
**Filters:** Exact or range filters via field-specific query parameters
**Date ranges:** Use `*_before` and `*_after` suffixes: `expiry_before=2026-12-31`

---

## 8. Naming Conventions

### Endpoint Naming
- **Use kebab-case** for URL paths: `/purchase-orders`, `/warehouse-locations`
- **Use plural nouns** for collection resources: `/products`, `/batches`
- **Use singular noun** for specific operations on a resource: `/product/{id}`
- **Sub-resources:** `/orders/{id}/items` for order items

### Field Naming
- **Use snake_case** for JSON field names: `product_name`, `expiry_date`
- **Boolean fields:** prefix with `is_` or `has_`: `is_active`, `has_expiry`
- **Date fields:** suffix with `_date` or `_at`: `expiry_date`, `created_at`
- **ID references:** suffix with `_id`: `product_id`, `warehouse_id`

---

## 9. Endpoint Index

### 9.0 Health

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/health` | Service health check | None |
| GET | `/api/v1/health` | Detailed health with DB status | None |

---

### 9.1 Authentication — `/api/v1/auth`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/v1/auth/login` | Login (business + consumer) | None | PLANNED |
| POST | `/api/v1/auth/register` | Consumer self-registration | None | PLANNED |
| POST | `/api/v1/auth/refresh` | Refresh access token | Refresh token | PLANNED |
| POST | `/api/v1/auth/logout` | Logout / invalidate token | Bearer | PLANNED |
| POST | `/api/v1/auth/change-password` | Change own password | Bearer | PLANNED |
| POST | `/api/v1/auth/request-password-reset` | Request password reset | None | PLANNED |
| POST | `/api/v1/auth/confirm-password-reset` | Confirm password reset | None | PLANNED |

---

### 9.2 Users — `/api/v1/users`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/users` | List users | Admin | PLANNED |
| POST | `/api/v1/users` | Create staff user | Admin | PLANNED |
| GET | `/api/v1/users/{id}` | Get user by ID | Admin/Self | PLANNED |
| PUT | `/api/v1/users/{id}` | Update user | Admin/Self | PLANNED |
| DELETE | `/api/v1/users/{id}` | Deactivate user | Admin | PLANNED |
| GET | `/api/v1/users/me` | Get current user profile | Bearer | PLANNED |
| PATCH | `/api/v1/users/me` | Update own profile | Bearer | PLANNED |

---

### 9.3 Products — `/api/v1/products`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/products` | List products | Bearer | PLANNED |
| POST | `/api/v1/products` | Create product | Admin/Manager | PLANNED |
| GET | `/api/v1/products/{id}` | Get product | Bearer | PLANNED |
| PUT | `/api/v1/products/{id}` | Update product | Admin/Manager | PLANNED |
| DELETE | `/api/v1/products/{id}` | Deactivate product | Admin | PLANNED |
| GET | `/api/v1/products/{id}/batches` | Get product batches | Bearer | PLANNED |

---

### 9.4 Categories — `/api/v1/categories`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/categories` | List categories | Bearer | PLANNED |
| POST | `/api/v1/categories` | Create category | Admin/Manager | PLANNED |
| GET | `/api/v1/categories/{id}` | Get category | Bearer | PLANNED |
| PUT | `/api/v1/categories/{id}` | Update category | Admin/Manager | PLANNED |
| DELETE | `/api/v1/categories/{id}` | Delete category | Admin | PLANNED |

---

### 9.5 Suppliers — `/api/v1/suppliers`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/suppliers` | List suppliers | Bearer | PLANNED |
| POST | `/api/v1/suppliers` | Create supplier | Admin/Manager | PLANNED |
| GET | `/api/v1/suppliers/{id}` | Get supplier | Bearer | PLANNED |
| PUT | `/api/v1/suppliers/{id}` | Update supplier | Admin/Manager | PLANNED |
| DELETE | `/api/v1/suppliers/{id}` | Deactivate supplier | Admin | PLANNED |

---

### 9.6 Purchase Orders — `/api/v1/purchase-orders`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/purchase-orders` | List purchase orders | Bearer | PLANNED |
| POST | `/api/v1/purchase-orders` | Create purchase order | Admin/Manager | PLANNED |
| GET | `/api/v1/purchase-orders/{id}` | Get purchase order | Bearer | PLANNED |
| PUT | `/api/v1/purchase-orders/{id}` | Update purchase order | Admin/Manager | PLANNED |
| POST | `/api/v1/purchase-orders/{id}/receive` | Receive stock | Staff+ | PLANNED |
| GET | `/api/v1/purchase-orders/{id}/items` | Get order items | Bearer | PLANNED |

---

### 9.7 Warehouses — `/api/v1/warehouses`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/warehouses` | List warehouses | Bearer | PLANNED |
| POST | `/api/v1/warehouses` | Create warehouse | Admin | PLANNED |
| GET | `/api/v1/warehouses/{id}` | Get warehouse | Bearer | PLANNED |
| PUT | `/api/v1/warehouses/{id}` | Update warehouse | Admin | PLANNED |
| GET | `/api/v1/warehouses/{id}/locations` | List warehouse locations | Bearer | PLANNED |
| POST | `/api/v1/warehouses/{id}/locations` | Add warehouse location | Admin | PLANNED |

---

### 9.8 Inventory — `/api/v1/inventory`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/inventory` | List inventory items | Bearer | PLANNED |
| GET | `/api/v1/inventory/{id}` | Get inventory item | Bearer | PLANNED |
| PATCH | `/api/v1/inventory/{id}/adjust` | Manual stock adjustment | Admin/Manager | PLANNED |
| GET | `/api/v1/inventory/low-stock` | List low stock items | Bearer | PLANNED |
| GET | `/api/v1/inventory/expiring-soon` | Items expiring soon | Bearer | PLANNED |
| GET | `/api/v1/inventory/transactions` | Inventory transaction log | Bearer | PLANNED |

---

### 9.9 Batches — `/api/v1/batches`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/batches` | List batches | Bearer | PLANNED |
| POST | `/api/v1/batches` | Create batch | Admin/Manager | PLANNED |
| GET | `/api/v1/batches/{id}` | Get batch | Bearer | PLANNED |
| PUT | `/api/v1/batches/{id}` | Update batch | Admin/Manager | PLANNED |
| GET | `/api/v1/batches/{id}/inventory` | Get batch inventory | Bearer | PLANNED |

---

### 9.10 FEFO — `/api/v1/fefo`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/fefo/pick-list` | Get FEFO-ordered pick list for product | Bearer | PLANNED |
| GET | `/api/v1/fefo/expiry-report` | Expiry risk report | Bearer | PLANNED |

---

### 9.11 Orders — `/api/v1/orders`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/orders` | List orders | Bearer | PLANNED |
| POST | `/api/v1/orders` | Create order | Consumer | PLANNED |
| GET | `/api/v1/orders/{id}` | Get order | Bearer | PLANNED |
| PATCH | `/api/v1/orders/{id}/status` | Update order status | Staff+ | PLANNED |
| GET | `/api/v1/orders/{id}/items` | Get order items | Bearer | PLANNED |

---

### 9.12 Pantry — `/api/v1/pantry`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/pantry` | Get user's pantry | Consumer | PLANNED |
| POST | `/api/v1/pantry/items` | Add item to pantry | Consumer | PLANNED |
| GET | `/api/v1/pantry/items/{id}` | Get pantry item | Consumer | PLANNED |
| PUT | `/api/v1/pantry/items/{id}` | Update pantry item | Consumer | PLANNED |
| DELETE | `/api/v1/pantry/items/{id}` | Remove from pantry | Consumer | PLANNED |
| GET | `/api/v1/pantry/expiring` | Items expiring soon | Consumer | PLANNED |

---

### 9.13 Scanning — `/api/v1/scanning`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| POST | `/api/v1/scanning/barcode` | Lookup product by barcode | Consumer | PLANNED |
| POST | `/api/v1/scanning/ocr` | Submit image for OCR processing | Consumer | PLANNED |

---

### 9.14 Notifications — `/api/v1/notifications`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/notifications` | List user notifications | Bearer | PLANNED |
| PATCH | `/api/v1/notifications/{id}/read` | Mark as read | Bearer | PLANNED |
| POST | `/api/v1/notifications/register-token` | Register FCM device token | Bearer | PLANNED |

---

### 9.15 Analytics — `/api/v1/analytics`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/analytics/dashboard` | Business dashboard summary | Admin/Manager | PLANNED |
| GET | `/api/v1/analytics/inventory-value` | Total inventory value | Admin/Manager | PLANNED |
| GET | `/api/v1/analytics/expiry-risk` | Expiry risk overview | Admin/Manager | PLANNED |
| GET | `/api/v1/analytics/sales-trend` | Sales trend data | Admin/Manager | PLANNED |

---

### 9.16 AI — `/api/v1/ai`

| Method | Path | Description | Auth | Status |
|--------|------|-------------|------|--------|
| GET | `/api/v1/ai/recommendations` | Get AI recommendations | Admin/Manager | PLANNED |
| GET | `/api/v1/ai/demand-forecast/{product_id}` | Demand forecast for product | Admin/Manager | PLANNED |
| GET | `/api/v1/ai/stockout-risk` | Stockout risk predictions | Admin/Manager | PLANNED |
| GET | `/api/v1/ai/waste-risk` | Waste risk predictions | Admin/Manager | PLANNED |
| POST | `/api/v1/ai/recommendations/{id}/approve` | Approve AI recommendation | Admin/Manager | PLANNED |
| POST | `/api/v1/ai/recommendations/{id}/dismiss` | Dismiss AI recommendation | Admin/Manager | PLANNED |

---

## 10. Health Endpoint (Implemented)

```
GET /health
```

**Response:**
```json
{
  "service": "avenzo-backend",
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-08-15T13:00:00Z"
}
```

This endpoint is unauthenticated and used for:
- Load balancer health checks
- CI/CD deployment verification
- Uptime monitoring

---

## 11. Rate Limiting (Planned)

Rate limiting will be applied per user/IP:
- Default: 100 requests/minute
- Auth endpoints: 10 requests/minute (brute force protection)
- OCR/Scanning: 20 requests/minute (resource-intensive)

Headers returned:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1723730400
```

---

*API Design Document — AVENZO Phase 0 Foundation*
