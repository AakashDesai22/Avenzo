/**
 * AVENZO Business Web — Closed-Loop Waste & Utilization Analytics API Wrapper
 */

import { apiGet, ApiResponse } from './client';

export interface SpoilageProductSummary {
  product_id: string;
  product_name: string;
  sku: string;
  category_name: string;
  discarded_quantity: number;
  discard_events_count: number;
}

export interface BusinessWasteAnalytics {
  total_warehouse_expired_units: number;
  total_capital_lost_expired: number;
  total_consumer_reported_discards: number;
  total_consumer_reported_consumptions: number;
  overall_inventory_waste_percentage: number;
  top_spoilage_products: SpoilageProductSummary[];
  has_sufficient_business_data: boolean;
}

export async function getBusinessWasteAnalyticsApi(): Promise<ApiResponse<BusinessWasteAnalytics>> {
  return apiGet<BusinessWasteAnalytics>('/analytics/business/waste');
}
