/**
 * AVENZO Business Web — Warehouse, Batch & Inventory Types
 */

import { Product } from './products';
import { Supplier } from './suppliers';

export interface WarehouseLocation {
  id: string;
  warehouse_id: string;
  location_code: string;
  description?: string;
  is_active: boolean;
}

export interface Warehouse {
  id: string;
  name: string;
  address?: string;
  city?: string;
  is_active: boolean;
  locations?: WarehouseLocation[];
}

export interface Batch {
  id: string;
  product_id: string;
  product?: Product;
  batch_number: string;
  manufacturing_date?: string;
  expiry_date?: string;
  supplier_id?: string;
  supplier?: Supplier;
  initial_quantity: number;
  status: string; // active, expired, depleted, recalled
  notes?: string;
  created_at?: string;
}

export interface BatchCreate {
  product_id: string;
  batch_number: string;
  manufacturing_date?: string;
  expiry_date?: string;
  supplier_id?: string;
  initial_quantity?: number;
  notes?: string;
}

export interface Inventory {
  id: string;
  product_id: string;
  product?: Product;
  batch_id: string;
  batch?: Batch;
  warehouse_id: string;
  warehouse?: Warehouse;
  location_id?: string;
  location?: WarehouseLocation;
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  created_at?: string;
  updated_at?: string;
}

export interface InventoryAdjustRequest {
  product_id: string;
  batch_id: string;
  warehouse_id: string;
  location_id?: string;
  quantity_change: number;
  transaction_type: string; // RECEIPT, ADJUSTMENT, DAMAGE, EXPIRY, etc.
  notes?: string;
}

export interface InventoryTransaction {
  id: string;
  inventory_id: string;
  transaction_type: string;
  quantity_change: number;
  quantity_before: number;
  quantity_after: number;
  reference_id?: string;
  reference_type?: string;
  notes?: string;
  performed_by?: string;
  created_at: string;
}
