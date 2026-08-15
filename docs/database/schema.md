# AVENZO — Database Schema Design

> Document Status: **ACTIVE — Phase 1 Implemented**
> Last Updated: 2026-08-15
> Database: PostgreSQL 16
> ORM: SQLAlchemy 2.x (asyncpg)
> Migrations: Alembic

---

## 1. Implementation Summary

| Table Name | Entity | Status | Phase Introduced |
|------------|--------|--------|-------------------|
| `users` | User Accounts | ✅ **IMPLEMENTED** | Phase 1 |
| `roles` | System Roles | ✅ **IMPLEMENTED** | Phase 1 |
| `permissions` | Granular Permissions | ✅ **IMPLEMENTED** | Phase 1 |
| `role_permissions` | RBAC Mapping | ✅ **IMPLEMENTED** | Phase 1 |
| `categories` | Product Categories | ✅ **IMPLEMENTED** | Phase 1 |
| `brands` | Product Brands | ✅ **IMPLEMENTED** | Phase 1 |
| `products` | Product Master Catalogue | ✅ **IMPLEMENTED** | Phase 1 |
| `suppliers` | Master Suppliers | ✅ **IMPLEMENTED** | Phase 1 |
| `warehouses` | Warehouse Facilities | ✅ **IMPLEMENTED** | Phase 1 |
| `warehouse_locations` | Bin / Shelf Locations | ✅ **IMPLEMENTED** | Phase 1 |
| `batches` | Product Batches & Expiry | ✅ **IMPLEMENTED** | Phase 1 |
| `inventory` | Stock Balances | ✅ **IMPLEMENTED** | Phase 1 |
| `inventory_transactions` | Audit Log Movements | ✅ **IMPLEMENTED** | Phase 1 |
| `purchase_orders` | Supplier POs | ⏳ **PLANNED** | Phase 2 |
| `purchase_order_items` | PO Item Details | ⏳ **PLANNED** | Phase 2 |
| `orders` | Consumer / B2B Orders | ⏳ **PLANNED** | Phase 3 |
| `order_items` | Order Item Details | ⏳ **PLANNED** | Phase 3 |
| `consumer_pantry` | Consumer Pantry | ⏳ **PLANNED** | Phase 3 |
| `pantry_items` | Pantry Items | ⏳ **PLANNED** | Phase 3 |
| `notifications` | System Notifications | ⏳ **PLANNED** | Phase 6 |
| `ai_recommendations` | AI Output Logs | ⏳ **PLANNED** | Phase 5 |

---

## 2. Design Principles

1. **UUID primary keys** — All tables use UUID as primary key (`uuid4`)
2. **Audit timestamps** — All tables include `created_at` and `updated_at` (UTC timezone)
3. **Soft deletes** — Managed via `is_deleted` + `deleted_at`
4. **Foreign key constraints** — Enforced at database level with indexes on foreign keys
5. **AI advisory data** — AI outputs stored separately, never overwrite authoritative database records

---

## 3. Implemented Entity Definitions (Phase 1)

### 3.1 User Management & RBAC

#### `users`
- `id` (UUID, PK)
- `email` (VARCHAR 255, Unique, Index)
- `password_hash` (VARCHAR 255, bcrypt hashed)
- `first_name` (VARCHAR 100), `last_name` (VARCHAR 100)
- `phone` (VARCHAR 20, Nullable)
- `role_id` (FK -> roles.id)
- `user_type` ('business' or 'consumer')
- `is_active` (BOOLEAN, default True)
- `last_login_at` (TIMESTAMP TZ, Nullable)
- `fcm_token` (VARCHAR 500, Nullable)
- `created_at`, `updated_at`, `is_deleted`, `deleted_at`

#### `roles`
- `id` (UUID, PK)
- `name` ('ADMIN', 'BUSINESS_MANAGER', 'STAFF', 'CONSUMER', Unique)
- `description` (TEXT, Nullable)
- `created_at`, `updated_at`

#### `permissions` & `role_permissions`
- Standard permission definitions and mapping table.

### 3.2 Product Master

#### `categories`
- `id` (UUID, PK)
- `name` (VARCHAR 150, Index)
- `parent_id` (FK -> categories.id, Self-referential, Nullable)
- `description` (TEXT, Nullable)
- `is_active` (BOOLEAN, default True)
- `created_at`, `updated_at`

#### `brands`
- `id` (UUID, PK)
- `name` (VARCHAR 150, Unique, Index)
- `description` (TEXT, Nullable), `logo_url` (VARCHAR 500, Nullable)
- `created_at`, `updated_at`

#### `products`
- `id` (UUID, PK)
- `name` (VARCHAR 255, Index)
- `sku` (VARCHAR 100, Unique, Index)
- `barcode` (VARCHAR 100, Unique, Index, Nullable)
- `category_id` (FK -> categories.id)
- `brand_id` (FK -> brands.id, Nullable)
- `unit_of_measure` (VARCHAR 50, default 'units')
- `unit_price` (NUMERIC 12,2), `cost_price` (NUMERIC 12,2, Nullable)
- `reorder_point` (INT, Nullable), `reorder_quantity` (INT, Nullable)
- `shelf_life_days` (INT, Nullable), `has_expiry` (BOOLEAN, default True)
- `image_url` (VARCHAR 500, Nullable), `is_active` (BOOLEAN, default True)
- `created_by` (FK -> users.id, Nullable)
- `created_at`, `updated_at`, `is_deleted`, `deleted_at`

### 3.3 Warehouses

#### `warehouses`
- `id` (UUID, PK), `name` (VARCHAR 150, Index), `address` (TEXT), `city` (VARCHAR 100), `is_active` (BOOLEAN, default True), `created_at`, `updated_at`

#### `warehouse_locations`
- `id` (UUID, PK), `warehouse_id` (FK -> warehouses.id), `location_code` (VARCHAR 50, Index), `description` (TEXT), `is_active` (BOOLEAN), `created_at`, `updated_at`
- Constraint: UNIQUE(`warehouse_id`, `location_code`)

### 3.4 Suppliers

#### `suppliers`
- `id` (UUID, PK), `name` (VARCHAR 255, Index), `contact_person`, `email`, `phone`, `address`, `city`, `country`, `is_active`, `created_at`, `updated_at`, `is_deleted`, `deleted_at`

### 3.5 Inventory & Batches

#### `batches`
- `id` (UUID, PK)
- `product_id` (FK -> products.id, Index)
- `batch_number` (VARCHAR 100, Index)
- `manufacturing_date` (DATE, Nullable)
- `expiry_date` (DATE, Index, Nullable)
- `supplier_id` (FK -> suppliers.id, Nullable)
- `initial_quantity` (INT, default 0)
- `status` ('active', 'expired', 'depleted', 'recalled')
- `notes` (TEXT), `created_by` (FK -> users.id, Nullable)
- `created_at`, `updated_at`
- Constraint: UNIQUE(`product_id`, `batch_number`)

#### `inventory`
- `id` (UUID, PK)
- `product_id` (FK -> products.id, Index)
- `batch_id` (FK -> batches.id, Index)
- `warehouse_id` (FK -> warehouses.id, Index)
- `location_id` (FK -> warehouse_locations.id, Nullable)
- `quantity_on_hand` (INT, default 0)
- `quantity_reserved` (INT, default 0)
- `created_at`, `updated_at`
- Constraint: UNIQUE(`batch_id`, `warehouse_id`, `location_id`)
- Property: `quantity_available = quantity_on_hand - quantity_reserved`

#### `inventory_transactions`
- `id` (UUID, PK)
- `inventory_id` (FK -> inventory.id, Index)
- `transaction_type` ('RECEIPT', 'ADJUSTMENT', 'TRANSFER', 'RESERVATION', 'RELEASE', 'SALE', 'DAMAGE', 'EXPIRY', Index)
- `quantity_change` (INT), `quantity_before` (INT), `quantity_after` (INT)
- `reference_id` (UUID, Nullable), `reference_type` (VARCHAR 50, Nullable)
- `notes` (TEXT), `performed_by` (FK -> users.id, Nullable)
- `created_at` (TIMESTAMP TZ, Index)

---

## 4. Deferred / Planned Entities

See Phase 2+ roadmap for Purchase Orders, Consumer Pantry, B2B Orders, FCM Notifications, and AI Output tables.
