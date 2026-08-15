/**
 * AVENZO Business Web — Expiry & Risk Types
 */

export interface ExpirySummary {
  warehouse_id?: string;
  category_id?: string;
  total_items_tracked: number;
  safe_quantity: number;
  expiring_soon_quantity: number;
  critical_quantity: number;
  expired_quantity: number;
  non_expiry_quantity: number;
  safe_batches_count: number;
  expiring_soon_batches_count: number;
  critical_batches_count: number;
  expired_batches_count: number;
}

export interface InventoryRiskMetrics {
  warehouse_id?: string;
  total_stock_quantity: number;
  near_expiry_quantity: number;
  critical_expiry_quantity: number;
  expired_quantity: number;
  expiry_exposure_percentage: number;
  capital_exposure_at_risk: number | string; // sum(quantity * cost_price)
  potential_sales_exposure: number | string; // sum(quantity * unit_price)
}
