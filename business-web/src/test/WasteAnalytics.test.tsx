import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AnalyticsPage } from '../pages/AnalyticsPage';
import { AuthContext, AuthContextType } from '../context/AuthContext';
import { UserRoleName } from '../types/auth';

vi.mock('../api/analytics.api', () => ({
  getBusinessWasteAnalyticsApi: vi.fn().mockResolvedValue({
    success: true,
    data: {
      total_warehouse_expired_units: 50,
      total_capital_lost_expired: 1250.0,
      total_consumer_reported_discards: 12.0,
      total_consumer_reported_consumptions: 88.0,
      overall_inventory_waste_percentage: 4.5,
      top_spoilage_products: [
        {
          product_id: 'p1',
          product_name: 'Organic Milk 1L',
          sku: 'DAIRY-MILK-01',
          category_name: 'Dairy',
          discarded_quantity: 12.0,
          discard_events_count: 3,
        },
      ],
      has_sufficient_business_data: true,
    },
  }),
}));

vi.mock('../api/expiry.api', () => ({
  getExpirySummaryApi: vi.fn().mockResolvedValue({
    success: true,
    data: {
      safe_quantity: 1000,
      expiring_soon_quantity: 100,
      critical_quantity: 20,
      expired_quantity: 50,
      total_items_tracked: 1170,
    },
  }),
  getRiskMetricsApi: vi.fn().mockResolvedValue({
    success: true,
    data: {
      capital_exposure_at_risk: 1250.0,
      potential_sales_exposure: 2000.0,
      expiry_exposure_percentage: 4.5,
    },
  }),
}));

vi.mock('../api/inventory.api', () => ({
  getBatchesApi: vi.fn().mockResolvedValue({ success: true, data: [] }),
  getInventoryApi: vi.fn().mockResolvedValue({ success: true, data: [] }),
  getWarehousesApi: vi.fn().mockResolvedValue({ success: true, data: [] }),
  getInventoryTransactionsApi: vi.fn().mockResolvedValue({ success: true, data: [] }),
}));

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

describe('AnalyticsPage Closed-Loop Waste Analytics', () => {
  it('renders closed-loop consumer waste & utilization analytics metrics', () => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const authValue = createMockAuthContext('STAFF');

    render(
      <QueryClientProvider client={queryClient}>
        <AuthContext.Provider value={authValue}>
          <BrowserRouter>
            <AnalyticsPage />
          </BrowserRouter>
        </AuthContext.Provider>
      </QueryClientProvider>
    );

    expect(screen.getByText('Analyst Intelligence Workspace')).toBeInTheDocument();
    expect(screen.getByText('Closed-Loop Consumer Waste & Utilization Analytics', { exact: false })).toBeInTheDocument();
  });
});
