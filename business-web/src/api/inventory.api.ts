/**
 * AVENZO Business Web — Inventory, Batches, Warehouses API Wrapper
 */

import { apiGet, apiPost, ApiResponse } from './client';
import {
  Warehouse,
  WarehouseLocation,
  Batch,
  BatchCreate,
  Inventory,
  InventoryAdjustRequest,
  InventoryTransaction,
} from '../types/inventory';

export async function getWarehousesApi(): Promise<ApiResponse<Warehouse[]>> {
  return apiGet<Warehouse[]>('/warehouses');
}

export async function createWarehouseLocationApi(
  warehouseId: string,
  data: { location_code: string; description?: string }
): Promise<ApiResponse<WarehouseLocation>> {
  return apiPost<WarehouseLocation>(`/warehouses/${warehouseId}/locations`, data);
}

export async function getBatchesApi(params?: {
  product_id?: string;
  status_filter?: string;
}): Promise<ApiResponse<Batch[]>> {
  return apiGet<Batch[]>('/batches', params);
}

export async function createBatchApi(data: BatchCreate): Promise<ApiResponse<Batch>> {
  return apiPost<Batch>('/batches', data);
}

export async function getInventoryApi(params?: {
  warehouse_id?: string;
  product_id?: string;
  batch_id?: string;
}): Promise<ApiResponse<Inventory[]>> {
  return apiGet<Inventory[]>('/inventory', params);
}

export async function adjustInventoryApi(data: InventoryAdjustRequest): Promise<ApiResponse<Inventory>> {
  return apiPost<Inventory>('/inventory/adjust', data);
}

export async function getInventoryTransactionsApi(params?: {
  inventory_id?: string;
  skip?: number;
  limit?: number;
}): Promise<ApiResponse<InventoryTransaction[]>> {
  return apiGet<InventoryTransaction[]>('/inventory/transactions', params);
}

export interface BatchRecallImpact {
  batch_id: string;
  batch_number: string;
  product_id: string;
  product_name: string;
  is_already_recalled: boolean;
  affected_orders_count: number;
  affected_consumers_count: number;
  affected_pantry_items_count: number;
  notifications_sent_count: number;
  recalled_at?: string;
  recall_reason?: string;
}

export async function getBatchRecallImpactApi(batchId: string): Promise<ApiResponse<BatchRecallImpact>> {
  return apiGet<BatchRecallImpact>(`/batches/${batchId}/recall-impact`);
}

export async function recallBatchApi(
  batchId: string,
  data: { recall_reason: string; severity?: string }
): Promise<ApiResponse<BatchRecallImpact>> {
  return apiPost<BatchRecallImpact>(`/batches/${batchId}/recall`, data);
}
