/**
 * AVENZO Business Web — FEFO Intelligence API Wrapper
 */

import { apiGet, apiPost, ApiResponse } from './client';
import {
  FEFORankedBatch,
  FEFOAllocationRequest,
  FEFOAllocationPlan,
  FEFOVerificationRequest,
  FEFOVerificationResponse,
} from '../types/fefo';

export async function getFefoBatchesApi(
  product_id: string,
  warehouse_id?: string
): Promise<ApiResponse<FEFORankedBatch[]>> {
  return apiGet<FEFORankedBatch[]>('/fefo/batches', { product_id, warehouse_id });
}

export async function previewFefoAllocationApi(
  data: FEFOAllocationRequest
): Promise<ApiResponse<FEFOAllocationPlan>> {
  return apiPost<FEFOAllocationPlan>('/fefo/allocate', data);
}

export async function verifyFefoSelectionApi(
  data: FEFOVerificationRequest
): Promise<ApiResponse<FEFOVerificationResponse>> {
  return apiPost<FEFOVerificationResponse>('/fefo/verify-selection', data);
}
