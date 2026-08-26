/**
 * AVENZO Business Web — Phase 9D Inventory Manager Workspace Unit Test Suite
 * Verifies Inventory Manager Dashboard, Warehouse overview, receiving workflow,
 * batch management, inventory adjustments, audit movement history, and RBAC mutation restrictions.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from '../pages/DashboardPage';
import { WarehousesPage } from '../pages/WarehousesPage';
import { BatchesPage } from '../pages/BatchesPage';
import { InventoryPage } from '../pages/InventoryPage';
import { AuthContext, AuthContextType } from '../context/AuthContext';
import { UserRoleName } from '../types/auth';

const createMockAuthContext = (roleName: UserRoleName = 'BUSINESS_MANAGER'): AuthContextType => ({
  user: {
    id: 'user-manager-2002',
    email: 'manager@avenzo.com',
    first_name: 'Inventory',
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
  can: (capability) =>
    roleName === 'ADMIN' ||
    (roleName === 'BUSINESS_MANAGER' && capability !== 'manage_users' && capability !== 'view_analytics'),
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

describe('Phase 9D — Inventory Manager Workspace Unit Tests', () => {
  describe('Inventory Manager Dashboard', () => {
    it('renders dashboard with Inventory Manager welcome and operational shortcuts', () => {
      renderWithProviders(<DashboardPage />, 'BUSINESS_MANAGER');

      expect(screen.getByText(/Welcome back, Inventory Manager/i)).toBeInTheDocument();
      expect(screen.getAllByText('Inventory Manager').length).toBeGreaterThan(0);
      expect(screen.getByText('Warehouse Facilities')).toBeInTheDocument();
    });
  });

  describe('Warehouse Facilities Overview', () => {
    it('renders Warehouse Overview page header and storage bin controls', () => {
      renderWithProviders(<WarehousesPage />, 'BUSINESS_MANAGER');

      expect(screen.getByText('Warehouse Facilities')).toBeInTheDocument();
      expect(screen.getByText(/Multi-facility oversight, storage bins/i)).toBeInTheDocument();
    });
  });

  describe('Batch Management & Product Receiving', () => {
    it('renders Batches page with Receive Product Batch CTA for Inventory Manager', () => {
      renderWithProviders(<BatchesPage />, 'BUSINESS_MANAGER');

      expect(screen.getByText('Batch Management & Product Receiving')).toBeInTheDocument();
      expect(screen.getByText('Receive Product Batch')).toBeInTheDocument();
      expect(screen.getByText('Quick Batch Record')).toBeInTheDocument();
    });

    it('hides batch mutation CTAs for Analyst (STAFF) role', () => {
      renderWithProviders(<BatchesPage />, 'STAFF');

      expect(screen.queryByText('Receive Product Batch')).not.toBeInTheDocument();
      expect(screen.queryByText('Quick Batch Record')).not.toBeInTheDocument();
    });
  });

  describe('Inventory Operations & Audit Movement Log', () => {
    it('renders Inventory page with stock adjustment CTAs for Inventory Manager', () => {
      renderWithProviders(<InventoryPage />, 'BUSINESS_MANAGER');

      expect(screen.getByText('Inventory Operations')).toBeInTheDocument();
      expect(screen.getByText('Adjust Stock Level')).toBeInTheDocument();
      expect(screen.getByText('Receive Product Batch')).toBeInTheDocument();
      expect(screen.getByText(/Stock Balances & Location Bins/i)).toBeInTheDocument();
    });

    it('hides stock adjustment CTAs for Analyst (STAFF) role', () => {
      renderWithProviders(<InventoryPage />, 'STAFF');

      expect(screen.queryByText('Adjust Stock Level')).not.toBeInTheDocument();
      expect(screen.queryByText('Receive Product Batch')).not.toBeInTheDocument();
    });
  });
});
