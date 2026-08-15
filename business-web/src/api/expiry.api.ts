/**
 * AVENZO Business Web — Expiry & Risk Intelligence API Wrapper
 */

import { apiGet, ApiResponse } from './client';
import { ExpirySummary, InventoryRiskMetrics } from '../types/expiry';

export async function getExpirySummaryApi(params?: {
  warehouse_id?: string;
  category_id?: string;
}): Promise<ApiResponse<ExpirySummary>> {
  return apiGet<ExpirySummary>('/inventory/expiry-summary', params);
}

export async function getRiskMetricsApi(params?: {
  warehouse_id?: string;
}): Promise<ApiResponse<InventoryRiskMetrics>> {
  return apiGet<InventoryRiskMetrics>('/inventory/risk-metrics', params);
}
