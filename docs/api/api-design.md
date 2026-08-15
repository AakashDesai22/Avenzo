# AVENZO — REST API Specification

> Document Status: **ACTIVE — Phase 2 Implemented**
> Base URL: `/api/v1`
> Format: JSON (`Content-Type: application/json`)
> Authentication: Bearer JWT (`Authorization: Bearer <token>`)

---

## Response Structure

All endpoints return a standardized `ApiResponse[T]` envelope:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional operational summary",
  "error": null,
  "meta": null
}
```

---

## API Index

### 1. Authentication & Users
- `POST /api/v1/auth/register` — Self-registration
- `POST /api/v1/auth/login` — Authenticate and receive JWT tokens
- `POST /api/v1/auth/refresh` — Refresh access token
- `GET /api/v1/auth/me` — Authenticated current user profile
- `GET /api/v1/users` — List users (Admin/Manager)
- `GET /api/v1/users/roles` — List system roles (Admin/Manager)

### 2. Product Catalogue
- `GET /api/v1/categories` — List categories
- `POST /api/v1/categories` — Create category (Admin/Manager)
- `GET /api/v1/products` — List products (search, filter, paginate)
- `POST /api/v1/products` — Create Product Master (Admin/Manager)
- `PUT /api/v1/products/{id}` — Update product

### 3. Warehouses & Suppliers
- `GET /api/v1/warehouses` — List warehouses
- `POST /api/v1/warehouses/{id}/locations` — Add bin location to warehouse
- `GET /api/v1/suppliers` — List suppliers

### 4. Batches & Inventory
- `GET /api/v1/batches` — List product batches
- `POST /api/v1/batches` — Create batch (validates `expiry_date >= manufacturing_date`)
- `GET /api/v1/inventory` — List stock balances
- `POST /api/v1/inventory/adjust` — Adjust stock & log audit transaction
- `GET /api/v1/inventory/transactions` — Audit trail for stock movements

### 5. FEFO Intelligence (Phase 2)
- `GET /api/v1/fefo/batches?product_id={uuid}&warehouse_id={uuid}` — List pickable batches ranked by 5-level FEFO tie-breaking rules:
  1. `expiry_date ASC`
  2. `manufacturing_date ASC`
  3. `created_at ASC`
  4. `quantity_available DESC`
  5. `batch.id ASC`
- `POST /api/v1/fefo/allocate` — **READ-ONLY FEFO Allocation Preview**. Calculates stock picking breakdown without mutating stock or reserving inventory.
- `POST /api/v1/fefo/verify-selection` — Verifies batch picking compliance and logs `FEFO_VIOLATION` audit transactions when earlier-expiring available stock is bypassed.

### 6. Expiry Intelligence & Risk (Phase 2)
- `GET /api/v1/inventory/expiry-summary` — Aggregated stock breakdown by classification (`SAFE`, `EXPIRING_SOON`, `CRITICAL`, `EXPIRED`, `N/A`).
- `GET /api/v1/inventory/risk-metrics` — Risk metrics:
  - `near_expiry_quantity` (DTE <= 30 days)
  - `critical_expiry_quantity` (DTE <= 7 days)
  - `expired_quantity` (DTE < 0)
  - `expiry_exposure_percentage`
  - `capital_exposure_at_risk` (`sum(qty * cost_price)`)
  - `potential_sales_exposure` (`sum(qty * unit_price)`)
