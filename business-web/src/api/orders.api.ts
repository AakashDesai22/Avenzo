/**
 * AVENZO Business Web — Orders & Fulfillment API Client
 * Wraps backend order fulfillment endpoints (/api/v1/orders).
 */

import { apiGet, apiPost, ApiResponse } from './client';
import { Order, OrderBatchAllocation } from '../types/orders';

export async function listOrders(status?: string): Promise<ApiResponse<Order[]>> {
  return apiGet<Order[]>('/orders', { status });
}

export async function getOrderById(orderId: string): Promise<ApiResponse<Order>> {
  return apiGet<Order>(`/orders/${orderId}`);
}

export async function getOrderAllocations(orderId: string): Promise<ApiResponse<OrderBatchAllocation[]>> {
  return apiGet<OrderBatchAllocation[]>(`/orders/${orderId}/allocations`);
}

export async function confirmOrder(orderId: string): Promise<ApiResponse<Order>> {
  return apiPost<Order>(`/orders/${orderId}/confirm`);
}

export async function allocateOrderFefo(orderId: string): Promise<ApiResponse<Order>> {
  return apiPost<Order>(`/orders/${orderId}/allocate`);
}

export async function packOrder(orderId: string): Promise<ApiResponse<Order>> {
  return apiPost<Order>(`/orders/${orderId}/pack`);
}

export async function dispatchOrder(orderId: string): Promise<ApiResponse<Order>> {
  return apiPost<Order>(`/orders/${orderId}/dispatch`);
}

export async function deliverOrder(orderId: string): Promise<ApiResponse<Order>> {
  return apiPost<Order>(`/orders/${orderId}/deliver`);
}

export async function cancelOrder(orderId: string): Promise<ApiResponse<Order>> {
  return apiPost<Order>(`/orders/${orderId}/cancel`);
}
