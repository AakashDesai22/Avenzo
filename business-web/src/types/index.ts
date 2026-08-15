/**
 * AVENZO Business Web — TypeScript Type Definitions
 * Core entity types matching the backend API schema.
 * Phase 1+ — expand as endpoints are implemented.
 */

// =============================================================================
// Common Types
// =============================================================================

export type UUID = string;

export type UserRole = 'admin' | 'manager' | 'staff' | 'consumer';

export type UserType = 'business' | 'consumer';

// =============================================================================
// User Types
// =============================================================================

export interface User {
  id: UUID;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  user_type: UserType;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// =============================================================================
// Product Types
// =============================================================================

export interface Category {
  id: UUID;
  name: string;
  parent_id: UUID | null;
  description: string | null;
  is_active: boolean;
}

export interface Brand {
  id: UUID;
  name: string;
  description: string | null;
}

export interface Product {
  id: UUID;
  name: string;
  description: string | null;
  sku: string;
  barcode: string | null;
  category_id: UUID;
  brand_id: UUID | null;
  unit_of_measure: string;
  unit_price: number;
  cost_price: number | null;
  reorder_point: number | null;
  has_expiry: boolean;
  shelf_life_days: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// =============================================================================
// Inventory Types
// =============================================================================

export type BatchStatus = 'active' | 'expired' | 'depleted' | 'recalled';

export interface Batch {
  id: UUID;
  product_id: UUID;
  batch_number: string;
  manufacturing_date: string | null;
  expiry_date: string | null;
  initial_quantity: number;
  status: BatchStatus;
}

export interface Inventory {
  id: UUID;
  product_id: UUID;
  batch_id: UUID;
  warehouse_id: UUID;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
}

// =============================================================================
// Order Types
// =============================================================================

export type OrderStatus =
  | 'pending'
  | 'confirmed'
  | 'picking'
  | 'shipped'
  | 'delivered'
  | 'cancelled';

export interface Order {
  id: UUID;
  order_number: string;
  consumer_id: UUID;
  status: OrderStatus;
  total_amount: number;
  placed_at: string;
}

// =============================================================================
// AI Types
// =============================================================================

export type RecommendationType =
  | 'reorder'
  | 'waste_risk'
  | 'stockout'
  | 'overstock';

export type RecommendationStatus = 'pending' | 'approved' | 'dismissed' | 'expired';

export interface AIRecommendation {
  id: UUID;
  recommendation_type: RecommendationType;
  product_id: UUID | null;
  message: string;
  confidence_score: number | null;
  status: RecommendationStatus;
  generated_at: string;
}

// =============================================================================
// Pagination
// =============================================================================

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}
