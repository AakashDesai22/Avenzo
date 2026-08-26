/**
 * AVENZO Business Web — Order & Fulfillment Types
 * Type definitions matching backend Order, OrderItem, and OrderBatchAllocation API contracts.
 */

import { Product } from './products';

export type OrderStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'ALLOCATED'
  | 'PACKED'
  | 'SHIPPED'
  | 'DELIVERED'
  | 'CANCELLED'
  | 'FAILED';

export type OrderFulfillmentStatus =
  | 'UNALLOCATED'
  | 'ALLOCATED'
  | 'PACKED'
  | 'SHIPPED'
  | 'DELIVERED';

export type PaymentStatus = 'UNPAID' | 'PAID' | 'REFUNDED';
export type PaymentMethod = 'MOCK_PAYMENT' | 'COD';

export interface OrderBatchAllocation {
  id: string;
  order_item_id: string;
  order_id: string;
  product_id: string;
  batch_id: string;
  inventory_id: string;
  allocated_quantity: number;
  batch_number?: string | null;
  expiry_date?: string | null;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  fulfillment_status: OrderFulfillmentStatus;
  product?: Product | null;
  allocations?: OrderBatchAllocation[];
  created_at: string;
  updated_at: string;
}

export interface Order {
  id: string;
  order_number: string;
  user_id: string;
  status: OrderStatus;
  payment_status: PaymentStatus;
  payment_method: PaymentMethod;
  subtotal: number;
  delivery_fee: number;
  total_amount: number;
  shipping_address: string;
  notes?: string | null;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}
