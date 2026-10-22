/**
 * AVENZO Business Web — WarehousesPage Unit Test Suite
 * Validates RBAC controls, creation buttons, empty state, error state, and facility listing.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { WarehousesPage } from '../pages/WarehousesPage';
import { AuthContext, AuthContextType } from '../context/AuthContext';
import { UserRoleName } from '../types/auth';
import * as inventoryApi from '../api/inventory.api';

vi.mock('../api/inventory.api', () => ({
  getWarehousesApi: vi.fn(),
  createWarehouseApi: vi.fn(),
  updateWarehouseApi: vi.fn(),
  deactivateWarehouseApi: vi.fn(),
  createWarehouseLocationApi: vi.fn(),
}));

const createMockAuthContext = (roleName: UserRoleName = 'BUSINESS_MANAGER'): AuthContextType => ({
  user: {
    id: 'user-manager-2002',
    email: 'manager@avenzo.com',
    first_name: 'Warehouse',
    last_name: 'Manager',
    user_type: 'business',
    is_active: true,
    role_id: 'role-manager-2',
    role: { id: 'role-manager-2', name: roleName },
  },
  isAuthenticated: true,
  isLoading: false,
  login: async () => {},
  logout: () => {},
  hasRole: (roles) => roles.includes(roleName),
  can: () => true,
});

const renderWithProviders = (ui: React.ReactNode, roleName: UserRoleName = 'BUSINESS_MANAGER') => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const authValue = createMockAuthContext(roleName);

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authValue}>
        <BrowserRouter>{ui}</BrowserRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
};

describe('WarehousesPage Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Add Warehouse" and "Create First Warehouse" for BUSINESS_MANAGER when list is empty', async () => {
    vi.mocked(inventoryApi.getWarehousesApi).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<WarehousesPage />, 'BUSINESS_MANAGER');

    // Header action button
    expect(await screen.findByRole('button', { name: /Add Warehouse/i })).toBeInTheDocument();

    // Empty state heading
    expect(await screen.findByText('No warehouse facilities configured')).toBeInTheDocument();

    // Empty state CTA button
    expect(await screen.findByRole('button', { name: /Create First Warehouse/i })).toBeInTheDocument();
  });

  it('renders "Add Warehouse" and "Create First Warehouse" for ADMIN', async () => {
    vi.mocked(inventoryApi.getWarehousesApi).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<WarehousesPage />, 'ADMIN');

    expect(await screen.findByRole('button', { name: /Add Warehouse/i })).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /Create First Warehouse/i })).toBeInTheDocument();
  });

  it('hides creation buttons and displays read-only notice for STAFF when empty', async () => {
    vi.mocked(inventoryApi.getWarehousesApi).mockResolvedValue({
      success: true,
      data: [],
    });

    renderWithProviders(<WarehousesPage />, 'STAFF');

    await screen.findByText('No warehouse facilities configured');

    // No creation buttons should be present
    expect(screen.queryByRole('button', { name: /Add Warehouse/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Create First Warehouse/i })).not.toBeInTheDocument();

    // Read-only explanation should be present
    expect(screen.getByText(/You have read-only access/i)).toBeInTheDocument();
  });

  it('renders explicit error banner when API returns error response', async () => {
    vi.mocked(inventoryApi.getWarehousesApi).mockResolvedValue({
      success: false,
      error: {
        code: 'HTTP_403',
        message: 'Forbidden: Insufficient privileges or invalid token',
      },
    });

    renderWithProviders(<WarehousesPage />, 'BUSINESS_MANAGER');

    expect(await screen.findByText('Unable to load warehouse facilities')).toBeInTheDocument();
    expect(
      screen.getByText('Forbidden: Insufficient privileges or invalid token')
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
  });

  it('renders warehouse cards when facilities exist', async () => {
    vi.mocked(inventoryApi.getWarehousesApi).mockResolvedValue({
      success: true,
      data: [
        {
          id: 'wh-1234-abcd',
          name: 'Main Distribution Center',
          city: 'Mumbai',
          address: 'Plot 10, Sector 4',
          is_active: true,
          created_at: '2026-10-01T00:00:00Z',
          locations: [
            { id: 'loc-1', warehouse_id: 'wh-1234-abcd', location_code: 'BIN-A1', description: 'Shelf 1', is_active: true },
          ],
        },
      ],
    });

    renderWithProviders(<WarehousesPage />, 'BUSINESS_MANAGER');

    expect(await screen.findByText('Main Distribution Center')).toBeInTheDocument();
    expect(screen.getByText(/Plot 10, Sector 4, Mumbai/i)).toBeInTheDocument();
    expect(screen.getByText('BIN-A1')).toBeInTheDocument();
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });
});
