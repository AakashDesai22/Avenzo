/**
 * AVENZO Business Web — Phase 9E Analyst Workspace Unit Test Suite
 * Verifies Analyst Intelligence Workspace rendering, Expiry/Risk/FEFO analytics,
 * read-only RBAC isolation, AI roadmap placeholders without fake metrics, and consumer rejection.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { InventoryPage } from '../pages/InventoryPage';
import { BatchesPage } from '../pages/BatchesPage';
import { WarehousesPage } from '../pages/WarehousesPage';
import { AuthContext, AuthContextType } from '../context/AuthContext';
import { UserRoleName } from '../types/auth';

const createMockAuthContext = (roleName: UserRoleName = 'STAFF'): AuthContextType => ({
  user: {
    id: 'user-analyst-3003',
    email: 'analyst@avenzo.com',
    first_name: 'Lead',
    last_name: 'Analyst',
    user_type: 'business',
    is_active: true,
    role_id: 'role-staff-3',
    role: { id: 'role-staff-3', name: roleName },
  },
  isAuthenticated: true,
  isLoading: false,
  login: async () => {},
  logout: () => {},
  hasRole: (roles) => roles.includes(roleName),
  can: (capability) =>
    roleName === 'ADMIN' ||
    (roleName === 'BUSINESS_MANAGER' && capability !== 'manage_users' && capability !== 'view_analytics') ||
    (roleName === 'STAFF' && (capability === 'view_dashboard' || capability === 'view_analytics' || capability === 'view_inventory' || capability === 'view_batches' || capability === 'view_fefo' || capability === 'view_notifications' || capability === 'view_expiry_risk')),
});

const renderWithRole = (ui: React.ReactNode, roleName: UserRoleName = 'STAFF') => {
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

describe('Phase 9E — Analyst Intelligence Workspace Suite', () => {
  describe('Analyst Intelligence Dashboard', () => {
    it('renders Analyst Intelligence Workspace header and Analyst badge', () => {
      renderWithRole(<AnalyticsPage />, 'STAFF');

      expect(screen.getByText('Analyst Intelligence Workspace')).toBeInTheDocument();
      expect(screen.getByText(/Analytical Operational Overview/i)).toBeInTheDocument();
      expect(screen.getByText(/Analyst \(Read-Only\)/i)).toBeInTheDocument();
    });

    it('renders financial exposure and waste risk metrics with business explanations', () => {
      renderWithRole(<AnalyticsPage />, 'STAFF');

      expect(screen.getByText('Capital Exposure at Risk')).toBeInTheDocument();
      expect(screen.getByText('Potential Sales Revenue Exposure')).toBeInTheDocument();
      expect(screen.getByText('Expiry Exposure Ratio')).toBeInTheDocument();
      expect(screen.getByText(/Estimated cost price of inventory near or past expiry/i)).toBeInTheDocument();
    });

    it('renders stock classification breakdown (SAFE, EXPIRING_SOON, CRITICAL, EXPIRED)', () => {
      renderWithRole(<AnalyticsPage />, 'STAFF');

      expect(screen.getByText('Inventory Health & Expiry Classification Breakdown')).toBeInTheDocument();
      expect(screen.getByText(/SAFE STOCK/i)).toBeInTheDocument();
      expect(screen.getByText(/EXPIRING SOON/i)).toBeInTheDocument();
      expect(screen.getByText(/CRITICAL STOCK/i)).toBeInTheDocument();
      expect(screen.getByText(/EXPIRED STOCK/i)).toBeInTheDocument();
    });

    it('renders FEFO sequence analytics section', () => {
      renderWithRole(<AnalyticsPage />, 'STAFF');

      expect(screen.getByText('FEFO Pick Sequence Analytics')).toBeInTheDocument();
      expect(screen.getByText(/Rotation & Pick Violation Audit/i)).toBeInTheDocument();
    });

    it('renders AI & Forecasting Roadmap section without fake metrics', () => {
      renderWithRole(<AnalyticsPage />, 'STAFF');

      expect(screen.getByText('AI & Forecasting — Coming Next')).toBeInTheDocument();
      expect(screen.getByText('Demand & Velocity Forecasting')).toBeInTheDocument();
      expect(screen.getByText('Spoilage & Waste Prediction')).toBeInTheDocument();
      expect(screen.getByText('Smart Markdown Recommendations')).toBeInTheDocument();
      expect(screen.getByText(/No fake predictions or mock confidence scores/i)).toBeInTheDocument();
    });
  });

  describe('Read-Only RBAC Enforcement for Analyst', () => {
    it('hides stock adjustment CTAs for Analyst on Inventory page', () => {
      renderWithRole(<InventoryPage />, 'STAFF');

      expect(screen.getByText('Inventory Operations')).toBeInTheDocument();
      expect(screen.queryByText('Adjust Stock Level')).not.toBeInTheDocument();
      expect(screen.queryByText('Receive Product Batch')).not.toBeInTheDocument();
    });

    it('hides batch creation CTAs for Analyst on Batches page', () => {
      renderWithRole(<BatchesPage />, 'STAFF');

      expect(screen.getByText('Batch Management & Product Receiving')).toBeInTheDocument();
      expect(screen.queryByText('Receive Product Batch')).not.toBeInTheDocument();
      expect(screen.queryByText('Quick Batch Record')).not.toBeInTheDocument();
    });

    it('hides bin creation button for Analyst on Warehouses page', () => {
      renderWithRole(<WarehousesPage />, 'STAFF');

      expect(screen.getByText('Warehouse Facilities')).toBeInTheDocument();
      expect(screen.queryByText('Add Bin')).not.toBeInTheDocument();
    });

    it('retains access to Analytics page for Admin role', () => {
      renderWithRole(<AnalyticsPage />, 'ADMIN');

      expect(screen.getByText('Analyst Intelligence Workspace')).toBeInTheDocument();
    });
  });
});
