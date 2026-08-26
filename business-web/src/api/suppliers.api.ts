/**
 * AVENZO Business Web — Supplier API Wrapper
 */

import { apiGet, apiPost, ApiResponse } from './client';
import { Supplier } from '../types/suppliers';

export async function getSuppliersApi(params?: {
  active_only?: boolean;
}): Promise<ApiResponse<Supplier[]>> {
  return apiGet<Supplier[]>('/suppliers', params);
}

export async function createSupplierApi(data: {
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  city?: string;
  country?: string;
}): Promise<ApiResponse<Supplier>> {
  return apiPost<Supplier>('/suppliers', data);
}
