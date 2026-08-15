/**
 * AVENZO Business Web — FEFO Intelligence Types
 */

export interface FEFORankedBatch {
  batch_id: string;
  batch_number: string;
  product_id: string;
  product_name: string;
  sku: string;
  has_expiry: boolean;
  manufacturing_date?: string;
  expiry_date?: string;
  days_to_expiry?: number;
  expiry_status: string; // SAFE, EXPIRING_SOON, CRITICAL, EXPIRED, N/A
  quantity_on_hand: number;
  quantity_reserved: number;
  quantity_available: number;
  warehouse_id: string;
  warehouse_name: string;
  location_id?: string;
  location_code?: string;
  fefo_rank: number;
}

export interface FEFOAllocationRequest {
  product_id: string;
  requested_quantity: number;
  warehouse_id?: string;
}

export interface FEFOBatchAllocationItem {
  batch_id: string;
  batch_number: string;
  manufacturing_date?: string;
  expiry_date?: string;
  days_to_expiry?: number;
  expiry_status: string;
  allocated_quantity: number;
  quantity_available: number;
  warehouse_id: string;
  warehouse_name: string;
  location_id?: string;
  location_code?: string;
  fefo_rank: number;
}

export interface FEFOAllocationPlan {
  product_id: string;
  product_name: string;
  sku: string;
  requested_quantity: number;
  allocated_total: number;
  remaining_unallocated: number;
  is_fully_allocated: boolean;
  allocations: FEFOBatchAllocationItem[];
}

export interface FEFOVerificationRequest {
  product_id: string;
  selected_batch_id: string;
  requested_quantity: number;
  warehouse_id?: string;
  override_reason?: string;
}

export interface FEFOVerificationResponse {
  is_compliant: boolean;
  violation_detected: boolean;
  warning_message?: string;
  selected_batch_id: string;
  selected_expiry_date?: string;
  earlier_available_batch_id?: string;
  earlier_available_expiry_date?: string;
  bypassed_earlier_quantity: number;
  audit_logged: boolean;
}
