/**
 * AVENZO Business Web — Batch Recall Workspace Vitest Suite
 * Verifies Batch Recall modal, impact preview, confirmation validation,
 * API dispatch, and RBAC authorization rules (ADMIN/BUSINESS_MANAGER vs STAFF).
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { BatchesPage } from '../pages/BatchesPage';
import { AuthContext } from '../context/AuthContext';
import * as inventoryApi from '../api/inventory.api';
import { Batch } from '../types/inventory';

const mockBatches: Batch[] = [
  {
    id: 'b-101',
    product_id: 'p-1',
    batch_number: 'BATCH-2026-ACTIVE',
    manufacturing_date: '2026-08-01',
    expiry_date: '2026-09-30',
    supplier_id: 's-1',
    initial_quantity: 100,
    status: 'active',
    product: {
      id: 'p-1',
      name: 'Organic Whole Milk',
      sku: 'MILK-ORG',
      unit_price: 5.0,
      category_id: 'cat-1',
      unit_of_measure: 'units',
      has_expiry: true,
      is_active: true,
    },
    created_at: '2026-08-01T10:00:00Z',
  },
  {
    id: 'b-102',
    product_id: 'p-2',
    batch_number: 'BATCH-2026-RECALLED',
    manufacturing_date: '2026-07-01',
    expiry_date: '2026-08-30',
    supplier_id: 's-1',
    initial_quantity: 50,
    status: 'recalled',
    product: {
      id: 'p-2',
      name: 'Greek Yogurt 500g',
      sku: 'YOG-500',
      unit_price: 3.5,
      category_id: 'cat-1',
      unit_of_measure: 'units',
      has_expiry: true,
      is_active: true,
    },
    created_at: '2026-07-01T10:00:00Z',
  },
];

const mockImpact: inventoryApi.BatchRecallImpact = {
  batch_id: 'b-101',
  batch_number: 'BATCH-2026-ACTIVE',
  product_id: 'p-1',
  product_name: 'Organic Whole Milk',
  is_already_recalled: false,
  affected_orders_count: 3,
  affected_consumers_count: 2,
  affected_pantry_items_count: 4,
  notifications_sent_count: 2,
};

function renderWithProviders(ui: React.ReactElement, role: string = 'ADMIN') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const authContextValue = {
    user: { id: 'usr-1', email: 'admin@avenzo.dev', first_name: 'Admin', last_name: 'User', role: { name: role } },
    token: 'token-123',
    login: vi.fn(),
    logout: vi.fn(),
    hasRole: (allowedRoles: string[]) => allowedRoles.includes(role),
    can: (perm: string) => perm === 'create_batches',
    isLoading: false,
  };

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authContextValue as any}>
        <BrowserRouter>{ui}</BrowserRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
}

describe('Batch Recall Workspace Vitest Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(inventoryApi, 'getBatchesApi').mockResolvedValue({ success: true, data: mockBatches });
    vi.spyOn(inventoryApi, 'getBatchRecallImpactApi').mockResolvedValue({ success: true, data: mockImpact });
    vi.spyOn(inventoryApi, 'recallBatchApi').mockResolvedValue({ success: true, data: mockImpact });
  });

  it('renders active batches and RECALLED badges correctly', async () => {
    renderWithProviders(<BatchesPage />, 'ADMIN');

    await waitFor(() => {
      expect(screen.getByText('BATCH-2026-ACTIVE')).toBeInTheDocument();
      expect(screen.getByText('BATCH-2026-RECALLED')).toBeInTheDocument();
    });

    // Should display RECALLED status badge for recalled batch
    expect(screen.getAllByText('RECALLED').length).toBeGreaterThanOrEqual(1);
  });

  it('allows ADMIN to open BatchRecallModal and view impact preview', async () => {
    renderWithProviders(<BatchesPage />, 'ADMIN');

    await waitFor(() => {
      expect(screen.getByText('BATCH-2026-ACTIVE')).toBeInTheDocument();
    });

    const recallBtn = screen.getByRole('button', { name: /Recall/i });
    fireEvent.click(recallBtn);

    await waitFor(() => {
      expect(screen.getByText(/Initiate Safety Recall/i)).toBeInTheDocument();
      expect(screen.getByText('Delivered Orders')).toBeInTheDocument();
    });
  });

  it('executes recall operation upon entering reason and "CONFIRMED RECALL"', async () => {
    renderWithProviders(<BatchesPage />, 'ADMIN');

    await waitFor(() => {
      expect(screen.getByText('BATCH-2026-ACTIVE')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Recall/i }));

    await waitFor(() => {
      expect(screen.getByText(/Initiate Safety Recall/i)).toBeInTheDocument();
    });

    const reasonInput = screen.getByPlaceholderText(/Contamination detected/i);
    const confirmInput = screen.getByPlaceholderText('CONFIRM RECALL');

    fireEvent.change(reasonInput, { target: { value: 'Quality inspection failure' } });
    fireEvent.change(confirmInput, { target: { value: 'CONFIRM RECALL' } });

    const submitBtn = screen.getByRole('button', { name: /Execute Safety Recall/i });
    expect(submitBtn).not.toBeDisabled();

    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(inventoryApi.recallBatchApi).toHaveBeenCalledWith('b-101', {
        recall_reason: 'Quality inspection failure',
        severity: 'HIGH',
      });
    });
  });

  it('hides Recall button for STAFF role', async () => {
    renderWithProviders(<BatchesPage />, 'STAFF');

    await waitFor(() => {
      expect(screen.getByText('BATCH-2026-ACTIVE')).toBeInTheDocument();
    });

    expect(screen.queryByRole('button', { name: /Recall/i })).not.toBeInTheDocument();
  });
});
