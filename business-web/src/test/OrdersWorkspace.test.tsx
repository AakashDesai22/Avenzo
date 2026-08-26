/**
 * AVENZO Business Web — Orders Workspace Vitest Test Suite
 * Tests Order Fulfillment Workspace rendering, status filter, modal opening,
 * FEFO pick list display, and role-based action visibility (ADMIN/BUSINESS_MANAGER vs STAFF).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { OrdersPage } from '../pages/OrdersPage';
import { AuthContext } from '../context/AuthContext';
import * as ordersApi from '../api/orders.api';
import { Order } from '../types/orders';

const mockOrders: Order[] = [
  {
    id: 'ord-1111-2222',
    order_number: 'ORD-2026-0001',
    user_id: 'usr-9999-8888',
    status: 'PENDING',
    payment_status: 'PAID',
    payment_method: 'MOCK_PAYMENT',
    subtotal: 20.0,
    delivery_fee: 2.5,
    total_amount: 22.5,
    shipping_address: '123 Main St, Austin TX',
    notes: 'Leave at front door',
    items: [
      {
        id: 'item-1',
        order_id: 'ord-1111-2222',
        product_id: 'prod-1',
        quantity: 5,
        unit_price: 4.0,
        total_price: 20.0,
        fulfillment_status: 'UNALLOCATED',
        product: {
          id: 'prod-1',
          name: 'Fresh Whole Milk 1L',
          sku: 'MILK-1L',
          unit_price: 4.0,
          category_id: 'cat-1',
          unit_of_measure: 'units',
          has_expiry: true,
          is_active: true,
        },
        allocations: [],
        created_at: '2026-08-26T10:00:00Z',
        updated_at: '2026-08-26T10:00:00Z',
      },
    ],
    created_at: '2026-08-26T10:00:00Z',
    updated_at: '2026-08-26T10:00:00Z',
  },
  {
    id: 'ord-3333-4444',
    order_number: 'ORD-2026-0002',
    user_id: 'usr-7777-6666',
    status: 'CONFIRMED',
    payment_status: 'PAID',
    payment_method: 'MOCK_PAYMENT',
    subtotal: 15.0,
    delivery_fee: 2.5,
    total_amount: 17.5,
    shipping_address: '456 Oak Ave, Dallas TX',
    items: [],
    created_at: '2026-08-26T10:05:00Z',
    updated_at: '2026-08-26T10:05:00Z',
  },
];

const mockAllocations = [
  {
    id: 'alloc-1',
    order_item_id: 'item-1',
    order_id: 'ord-1111-2222',
    product_id: 'prod-1',
    batch_id: 'batch-101',
    inventory_id: 'inv-202',
    allocated_quantity: 5,
    batch_number: 'B-MILK-101',
    expiry_date: '2026-09-15',
    created_at: '2026-08-26T10:00:00Z',
    updated_at: '2026-08-26T10:00:00Z',
  },
];

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0 },
    },
  });
}

function renderOrdersPageWithRole(roleName: 'ADMIN' | 'BUSINESS_MANAGER' | 'STAFF') {
  const queryClient = createTestQueryClient();
  const mockUser = {
    id: 'user-admin',
    email: 'admin@avenzo.com',
    first_name: 'Operational',
    last_name: 'User',
    user_type: 'business',
    is_active: true,
    role_id: 'r1',
    role: { id: 'r1', name: roleName },
  };

  const hasRole = (roles: string[]) => roles.includes(roleName);
  const can = (cap: string) => {
    if (roleName === 'STAFF') return cap === 'view_orders';
    return cap === 'view_orders' || cap === 'manage_fulfillment';
  };

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider
        value={{
          user: mockUser,
          isAuthenticated: true,
          isLoading: false,
          login: vi.fn(),
          logout: vi.fn(),
          hasRole,
          can: can as any,
        }}
      >
        <BrowserRouter>
          <OrdersPage />
        </BrowserRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}

describe('OrdersPage & Fulfillment Workspace Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(ordersApi, 'listOrders').mockResolvedValue({
      success: true,
      data: mockOrders,
    });
    vi.spyOn(ordersApi, 'getOrderAllocations').mockResolvedValue({
      success: true,
      data: mockAllocations,
    });
  });

  it('1. Renders workspace header and live metric cards', async () => {
    renderOrdersPageWithRole('ADMIN');
    expect(screen.getByText('Order Fulfillment Workspace')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('ORD-2026-0001')).toBeInTheDocument();
    });
    expect(screen.getAllByText('Pending').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Confirmed').length).toBeGreaterThan(0);
  });

  it('2. Renders operational order queue table items', async () => {
    renderOrdersPageWithRole('ADMIN');
    await waitFor(() => {
      expect(screen.getByText('ORD-2026-0001')).toBeInTheDocument();
      expect(screen.getByText('ORD-2026-0002')).toBeInTheDocument();
    });
    expect(screen.getByText('$22.50')).toBeInTheDocument();
    expect(screen.getByText('$17.50')).toBeInTheDocument();
  });

  it('3. Renders operational action buttons for ADMIN role', async () => {
    renderOrdersPageWithRole('ADMIN');
    await waitFor(() => {
      expect(screen.getByText('Confirm')).toBeInTheDocument();
      expect(screen.getByText('FEFO')).toBeInTheDocument();
    });
  });

  it('4. Hides operational action buttons for STAFF role (Read-Only Mode)', async () => {
    renderOrdersPageWithRole('STAFF');
    await waitFor(() => {
      expect(screen.getByText('ORD-2026-0001')).toBeInTheDocument();
    });
    expect(screen.queryByText('Confirm')).not.toBeInTheDocument();
    expect(screen.queryByText('FEFO')).not.toBeInTheDocument();
    expect(screen.getAllByText('Details').length).toBeGreaterThan(0);
  });

  it('5. Opens OrderDetailModal when clicking order details', async () => {
    renderOrdersPageWithRole('ADMIN');
    await waitFor(() => {
      expect(screen.getByText('ORD-2026-0001')).toBeInTheDocument();
    });

    const detailsButtons = screen.getAllByText('Details');
    fireEvent.click(detailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Order ORD-2026-0001')).toBeInTheDocument();
      expect(screen.getByText('Fresh Whole Milk 1L')).toBeInTheDocument();
      expect(screen.getByText('FEFO Batch Allocation Pick List')).toBeInTheDocument();
    });
  });

  it('6. Calls confirmOrder API when clicking Confirm', async () => {
    const confirmSpy = vi.spyOn(ordersApi, 'confirmOrder').mockResolvedValue({
      success: true,
      data: { ...mockOrders[0], status: 'CONFIRMED' },
    });

    renderOrdersPageWithRole('ADMIN');
    await waitFor(() => {
      expect(screen.getByText('Confirm')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Confirm'));

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalledWith('ord-1111-2222');
    });
  });

  it('7. Calls allocateOrderFefo API when clicking FEFO', async () => {
    const allocateSpy = vi.spyOn(ordersApi, 'allocateOrderFefo').mockResolvedValue({
      success: true,
      data: { ...mockOrders[1], status: 'ALLOCATED' },
    });

    renderOrdersPageWithRole('BUSINESS_MANAGER');
    await waitFor(() => {
      expect(screen.getByText('FEFO')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('FEFO'));

    await waitFor(() => {
      expect(allocateSpy).toHaveBeenCalledWith('ord-3333-4444');
    });
  });
});
