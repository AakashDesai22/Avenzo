/**
 * AVENZO Business Web — Product & Category Types
 */

export interface Category {
  id: string;
  name: string;
  description?: string;
  parent_id?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Brand {
  id: string;
  name: string;
  description?: string;
  logo_url?: string;
}

export interface Product {
  id: string;
  name: string;
  sku: string;
  barcode?: string;
  category_id: string;
  category?: Category;
  brand_id?: string;
  brand?: Brand;
  unit_of_measure: string;
  unit_price: number | string;
  cost_price?: number | string;
  reorder_point?: number;
  reorder_quantity?: number;
  shelf_life_days?: number;
  has_expiry: boolean;
  image_url?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ProductCreate {
  name: string;
  sku: string;
  barcode?: string;
  category_id: string;
  brand_id?: string;
  unit_of_measure?: string;
  unit_price: number | string;
  cost_price?: number | string;
  reorder_point?: number;
  reorder_quantity?: number;
  shelf_life_days?: number;
  has_expiry?: boolean;
}

export interface ProductUpdate {
  name?: string;
  barcode?: string;
  category_id?: string;
  brand_id?: string;
  unit_of_measure?: string;
  unit_price?: number | string;
  cost_price?: number | string;
  reorder_point?: number;
  reorder_quantity?: number;
  shelf_life_days?: number;
  has_expiry?: boolean;
  is_active?: boolean;
}

export interface CategoryCreate {
  name: string;
  description?: string;
  parent_id?: string;
}

export interface CategoryUpdate {
  name?: string;
  description?: string;
  parent_id?: string;
  is_active?: boolean;
}
