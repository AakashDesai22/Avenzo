# AVENZO — Database Schema Design

> Document Status: **DRAFT — Foundation Phase**
> Last Updated: 2026-08-15
> Database: PostgreSQL 15+
> ORM: SQLAlchemy (async)
> Migrations: Alembic

---

## 1. Design Principles

1. **UUID primary keys** — All tables use UUID as primary key (not auto-increment integers)
2. **Audit timestamps** — All tables include `created_at` and `updated_at` timestamps (UTC)
3. **Soft deletes** — Where data must be preserved, use `is_deleted` + `deleted_at`
4. **Status enums** — Status fields use string values defined in application layer
5. **Foreign key constraints** — Enforced at database level
6. **Normalization** — 3NF minimum; denormalize only when performance requires
7. **AI advisory data** — AI outputs stored separately, never overwrite authoritative records

---

## 2. Common Column Patterns

### Base Columns (all tables)
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
updated_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
```

### Soft Delete Columns (where applicable)
```sql
is_deleted  BOOLEAN NOT NULL DEFAULT FALSE
deleted_at  TIMESTAMP WITH TIME ZONE
deleted_by  UUID REFERENCES users(id)
```

---

## 3. Entity Definitions

---

### 3.1 User Management

#### `users`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, NOT NULL | Auto-generated |
| email | VARCHAR(255) | NOT NULL, UNIQUE | Login identifier |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hashed |
| first_name | VARCHAR(100) | NOT NULL | |
| last_name | VARCHAR(100) | NOT NULL | |
| phone | VARCHAR(20) | NULLABLE | Optional contact |
| role_id | UUID | FK → roles(id) | Assigned role |
| user_type | VARCHAR(20) | NOT NULL | 'business' or 'consumer' |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | Account status |
| last_login_at | TIMESTAMP TZ | NULLABLE | Last successful login |
| fcm_token | VARCHAR(500) | NULLABLE | Firebase push token |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |
| is_deleted | BOOLEAN | NOT NULL DEFAULT FALSE | |
| deleted_at | TIMESTAMP TZ | NULLABLE | |

#### `roles`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(50) | NOT NULL, UNIQUE | e.g., 'admin', 'manager' |
| description | TEXT | NULLABLE | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

Values: `admin`, `manager`, `staff`, `consumer`

#### `permissions`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(100) | NOT NULL, UNIQUE | e.g., 'inventory.write' |
| description | TEXT | NULLABLE | |
| created_at | TIMESTAMP TZ | NOT NULL | |

#### `role_permissions`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| role_id | UUID | FK → roles(id) | |
| permission_id | UUID | FK → permissions(id) | |
| PK | composite | (role_id, permission_id) | |

---

### 3.2 Product Catalogue

#### `brands`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(150) | NOT NULL, UNIQUE | |
| description | TEXT | NULLABLE | |
| logo_url | VARCHAR(500) | NULLABLE | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

#### `categories`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(150) | NOT NULL | |
| parent_id | UUID | FK → categories(id), NULLABLE | Self-referential hierarchy |
| description | TEXT | NULLABLE | |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

#### `products`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | |
| description | TEXT | NULLABLE | |
| sku | VARCHAR(100) | NOT NULL, UNIQUE | Stock Keeping Unit |
| barcode | VARCHAR(100) | NULLABLE, UNIQUE | EAN/UPC barcode |
| category_id | UUID | FK → categories(id), NOT NULL | |
| brand_id | UUID | FK → brands(id), NULLABLE | |
| unit_of_measure | VARCHAR(50) | NOT NULL | e.g., 'kg', 'units', 'liters' |
| unit_price | DECIMAL(12,2) | NOT NULL | Base selling price |
| cost_price | DECIMAL(12,2) | NULLABLE | Cost for margin calculation |
| reorder_point | INTEGER | NULLABLE | Trigger low-stock alert |
| reorder_quantity | INTEGER | NULLABLE | Suggested reorder quantity |
| shelf_life_days | INTEGER | NULLABLE | Expected product shelf life |
| has_expiry | BOOLEAN | NOT NULL DEFAULT TRUE | Does product expire? |
| image_url | VARCHAR(500) | NULLABLE | |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | |
| created_by | UUID | FK → users(id), NULLABLE | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |
| is_deleted | BOOLEAN | NOT NULL DEFAULT FALSE | |
| deleted_at | TIMESTAMP TZ | NULLABLE | |

---

### 3.3 Supplier Management

#### `suppliers`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(255) | NOT NULL | |
| contact_person | VARCHAR(150) | NULLABLE | |
| email | VARCHAR(255) | NULLABLE | |
| phone | VARCHAR(20) | NULLABLE | |
| address | TEXT | NULLABLE | |
| city | VARCHAR(100) | NULLABLE | |
| country | VARCHAR(100) | NULLABLE | |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |
| is_deleted | BOOLEAN | NOT NULL DEFAULT FALSE | |
| deleted_at | TIMESTAMP TZ | NULLABLE | |

#### `purchase_orders`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| order_number | VARCHAR(50) | NOT NULL, UNIQUE | Human-readable ref |
| supplier_id | UUID | FK → suppliers(id), NOT NULL | |
| status | VARCHAR(30) | NOT NULL | draft/sent/partial/received/cancelled |
| ordered_at | TIMESTAMP TZ | NULLABLE | When order was placed |
| expected_at | DATE | NULLABLE | Expected delivery date |
| received_at | TIMESTAMP TZ | NULLABLE | Actual delivery time |
| notes | TEXT | NULLABLE | |
| created_by | UUID | FK → users(id) | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

#### `purchase_order_items`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| purchase_order_id | UUID | FK → purchase_orders(id) NOT NULL | |
| product_id | UUID | FK → products(id) NOT NULL | |
| quantity_ordered | INTEGER | NOT NULL | |
| quantity_received | INTEGER | NOT NULL DEFAULT 0 | |
| unit_cost | DECIMAL(12,2) | NOT NULL | Agreed unit cost |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

---

### 3.4 Warehouse Management

#### `warehouses`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| name | VARCHAR(150) | NOT NULL | |
| address | TEXT | NULLABLE | |
| city | VARCHAR(100) | NULLABLE | |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

#### `warehouse_locations`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| warehouse_id | UUID | FK → warehouses(id) NOT NULL | |
| location_code | VARCHAR(50) | NOT NULL | e.g., 'A-01-02' |
| description | TEXT | NULLABLE | |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |
| UNIQUE | | (warehouse_id, location_code) | |

---

### 3.5 Batch & Inventory Management

#### `batches`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| product_id | UUID | FK → products(id) NOT NULL | |
| batch_number | VARCHAR(100) | NOT NULL | Manufacturer batch ID |
| manufacturing_date | DATE | NULLABLE | |
| expiry_date | DATE | NULLABLE | Critical for FEFO |
| supplier_id | UUID | FK → suppliers(id) NULLABLE | |
| purchase_order_id | UUID | FK → purchase_orders(id) NULLABLE | |
| initial_quantity | INTEGER | NOT NULL | Quantity received |
| status | VARCHAR(30) | NOT NULL | active/expired/depleted/recalled |
| notes | TEXT | NULLABLE | |
| created_by | UUID | FK → users(id) | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |
| UNIQUE | | (product_id, batch_number) | |

#### `inventory`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| product_id | UUID | FK → products(id) NOT NULL | |
| batch_id | UUID | FK → batches(id) NOT NULL | |
| warehouse_id | UUID | FK → warehouses(id) NOT NULL | |
| location_id | UUID | FK → warehouse_locations(id) NULLABLE | |
| quantity_on_hand | INTEGER | NOT NULL DEFAULT 0 | Current stock |
| quantity_reserved | INTEGER | NOT NULL DEFAULT 0 | Reserved for orders |
| UNIQUE | | (batch_id, warehouse_id, location_id) | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

**Computed:** `quantity_available = quantity_on_hand - quantity_reserved`

#### `inventory_transactions`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| inventory_id | UUID | FK → inventory(id) NOT NULL | |
| transaction_type | VARCHAR(50) | NOT NULL | receive/sale/adjustment/transfer/expired |
| quantity_change | INTEGER | NOT NULL | Positive = in, Negative = out |
| quantity_before | INTEGER | NOT NULL | Stock before transaction |
| quantity_after | INTEGER | NOT NULL | Stock after transaction |
| reference_id | UUID | NULLABLE | Order/PO/transfer ID |
| reference_type | VARCHAR(50) | NULLABLE | 'order', 'purchase_order', etc. |
| notes | TEXT | NULLABLE | |
| performed_by | UUID | FK → users(id) | |
| created_at | TIMESTAMP TZ | NOT NULL | Immutable — no updates |

---

### 3.6 Order Management

#### `orders`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| order_number | VARCHAR(50) | NOT NULL, UNIQUE | Human-readable ref |
| consumer_id | UUID | FK → users(id) NOT NULL | Customer |
| status | VARCHAR(30) | NOT NULL | pending/confirmed/picking/shipped/delivered/cancelled |
| total_amount | DECIMAL(12,2) | NOT NULL | |
| delivery_address | TEXT | NULLABLE | |
| notes | TEXT | NULLABLE | |
| placed_at | TIMESTAMP TZ | NOT NULL | |
| confirmed_at | TIMESTAMP TZ | NULLABLE | |
| delivered_at | TIMESTAMP TZ | NULLABLE | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

#### `order_items`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| order_id | UUID | FK → orders(id) NOT NULL | |
| product_id | UUID | FK → products(id) NOT NULL | |
| batch_id | UUID | FK → batches(id) NULLABLE | Assigned at picking |
| quantity | INTEGER | NOT NULL | |
| unit_price | DECIMAL(12,2) | NOT NULL | Price at time of order |
| total_price | DECIMAL(12,2) | NOT NULL | quantity × unit_price |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

---

### 3.7 Consumer Pantry

#### `consumer_pantries`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| consumer_id | UUID | FK → users(id) NOT NULL, UNIQUE | One pantry per user |
| name | VARCHAR(100) | NOT NULL DEFAULT 'My Pantry' | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

#### `pantry_items`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| pantry_id | UUID | FK → consumer_pantries(id) NOT NULL | |
| product_id | UUID | FK → products(id) NULLABLE | If from platform |
| order_item_id | UUID | FK → order_items(id) NULLABLE | If added via order |
| custom_product_name | VARCHAR(255) | NULLABLE | For manually added items |
| quantity | DECIMAL(10,2) | NOT NULL | |
| unit | VARCHAR(50) | NULLABLE | e.g., 'pieces', 'grams' |
| expiry_date | DATE | NULLABLE | |
| manufacturing_date | DATE | NULLABLE | |
| added_method | VARCHAR(30) | NOT NULL | 'order', 'manual', 'scan', 'ocr' |
| notes | TEXT | NULLABLE | |
| is_consumed | BOOLEAN | NOT NULL DEFAULT FALSE | |
| consumed_at | TIMESTAMP TZ | NULLABLE | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

---

### 3.8 Notifications

#### `notifications`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| user_id | UUID | FK → users(id) NOT NULL | |
| title | VARCHAR(255) | NOT NULL | |
| body | TEXT | NOT NULL | |
| notification_type | VARCHAR(50) | NOT NULL | expiry_warning/low_stock/order_update/etc. |
| reference_id | UUID | NULLABLE | Related entity ID |
| reference_type | VARCHAR(50) | NULLABLE | 'pantry_item', 'inventory', 'order' |
| is_read | BOOLEAN | NOT NULL DEFAULT FALSE | |
| read_at | TIMESTAMP TZ | NULLABLE | |
| is_sent | BOOLEAN | NOT NULL DEFAULT FALSE | Push sent? |
| sent_at | TIMESTAMP TZ | NULLABLE | |
| created_at | TIMESTAMP TZ | NOT NULL | |

---

### 3.9 AI / ML Data

#### `ai_recommendations`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| recommendation_type | VARCHAR(50) | NOT NULL | reorder/waste_risk/stockout/overstock |
| product_id | UUID | FK → products(id) NULLABLE | |
| warehouse_id | UUID | FK → warehouses(id) NULLABLE | |
| batch_id | UUID | FK → batches(id) NULLABLE | |
| message | TEXT | NOT NULL | Human-readable recommendation |
| metadata | JSONB | NULLABLE | Model output details |
| confidence_score | DECIMAL(5,4) | NULLABLE | 0.0000 to 1.0000 |
| status | VARCHAR(30) | NOT NULL DEFAULT 'pending' | pending/approved/dismissed/expired |
| reviewed_by | UUID | FK → users(id) NULLABLE | |
| reviewed_at | TIMESTAMP TZ | NULLABLE | |
| generated_at | TIMESTAMP TZ | NOT NULL | When AI produced this |
| expires_at | TIMESTAMP TZ | NULLABLE | Recommendation no longer valid after |
| created_at | TIMESTAMP TZ | NOT NULL | |
| updated_at | TIMESTAMP TZ | NOT NULL | |

#### `risk_scores`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| score_type | VARCHAR(50) | NOT NULL | inventory_risk/expiry_risk/demand_risk |
| product_id | UUID | FK → products(id) NULLABLE | |
| batch_id | UUID | FK → batches(id) NULLABLE | |
| score | DECIMAL(5,4) | NOT NULL | 0.0000 = no risk, 1.0000 = critical |
| risk_level | VARCHAR(20) | NOT NULL | low/medium/high/critical |
| computed_at | TIMESTAMP TZ | NOT NULL | When score was calculated |
| valid_until | TIMESTAMP TZ | NULLABLE | Score expiry |
| metadata | JSONB | NULLABLE | Score breakdown/contributing factors |
| created_at | TIMESTAMP TZ | NOT NULL | |

#### `demand_forecasts`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| product_id | UUID | FK → products(id) NOT NULL | |
| warehouse_id | UUID | FK → warehouses(id) NULLABLE | |
| forecast_date | DATE | NOT NULL | Date being forecasted |
| predicted_quantity | DECIMAL(10,2) | NOT NULL | |
| confidence_lower | DECIMAL(10,2) | NULLABLE | Lower bound |
| confidence_upper | DECIMAL(10,2) | NULLABLE | Upper bound |
| model_version | VARCHAR(50) | NULLABLE | Which model version produced this |
| generated_at | TIMESTAMP TZ | NOT NULL | |
| created_at | TIMESTAMP TZ | NOT NULL | |
| UNIQUE | | (product_id, warehouse_id, forecast_date) | |

#### `waste_predictions`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| product_id | UUID | FK → products(id) NOT NULL | |
| batch_id | UUID | FK → batches(id) NULLABLE | |
| predicted_waste_quantity | DECIMAL(10,2) | NOT NULL | |
| predicted_waste_value | DECIMAL(12,2) | NULLABLE | Estimated monetary loss |
| prediction_date | DATE | NOT NULL | |
| generated_at | TIMESTAMP TZ | NOT NULL | |
| created_at | TIMESTAMP TZ | NOT NULL | |

---

## 4. Relationships Summary

```
users ──── roles ──── role_permissions ──── permissions

products ──── categories (tree)
products ──── brands
products ──── batches ──── inventory ──── inventory_transactions
products ──── purchase_order_items ──── purchase_orders ──── suppliers

warehouses ──── warehouse_locations ──── inventory

users (consumer) ──── orders ──── order_items ──── products
users (consumer) ──── consumer_pantries ──── pantry_items

users ──── notifications

ai_recommendations ──── products
ai_recommendations ──── batches
risk_scores ──── products / batches
demand_forecasts ──── products
waste_predictions ──── products / batches
```

---

## 5. Indexes (Planned)

| Table | Index | Type | Reason |
|-------|-------|------|--------|
| users | email | UNIQUE | Login lookup |
| products | sku | UNIQUE | Product lookup |
| products | barcode | UNIQUE | Barcode scan lookup |
| batches | expiry_date | B-tree | FEFO sorting |
| batches | (product_id, batch_number) | UNIQUE | |
| inventory | (batch_id, warehouse_id) | B-tree | Stock queries |
| inventory_transactions | created_at | B-tree | Audit timeline |
| pantry_items | expiry_date | B-tree | Expiry alerts |
| notifications | (user_id, is_read) | B-tree | Unread count |
| ai_recommendations | status | B-tree | Pending recommendations |

---

## 6. Migration Status

| Entity Group | Schema Documented | Migration Created | Implemented |
|-------------|-------------------|-------------------|-------------|
| User Management | ✅ | ❌ | ❌ |
| Product Catalogue | ✅ | ❌ | ❌ |
| Supplier Management | ✅ | ❌ | ❌ |
| Warehouse Management | ✅ | ❌ | ❌ |
| Batch & Inventory | ✅ | ❌ | ❌ |
| Order Management | ✅ | ❌ | ❌ |
| Consumer Pantry | ✅ | ❌ | ❌ |
| Notifications | ✅ | ❌ | ❌ |
| AI/ML Data | ✅ | ❌ | ❌ |

---

*Database Schema Document — AVENZO Phase 0 Foundation*
