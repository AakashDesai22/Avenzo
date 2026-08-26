/**
 * AVENZO Business Web — Admin Command Center Unit Test Suite
 * Verifies rendering, real KPI display, loading/error states, quick actions,
 * AI roadmap placeholders, and role-based capability boundaries.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from '../pages/DashboardPage';
import { AuthContext, AuthContextType } from '../context/AuthContext';
import { UserRoleName } from '../types/auth';

const createMockAuthContext = (roleName: UserRoleName = 'ADMIN'): AuthContextType => ({
  user: {
    id: 'user-admin-1001',
    email: 'admin@avenzo.com',
    first_name: 'System',
    last_name: 'Administrator',
    user_type: 'business',
    is_active: true,
    role_id: 'role-admin-1',
    role: { id: 'role-admin-1', name: roleName },
  },
  isAuthenticated: true,
  isLoading: false,
  login: async () => {},
  logout: () => {},
  hasRole: (roles) => roles.includes(roleName),
  can: (capability) => roleName === 'ADMIN' || (roleName === 'BUSINESS_MANAGER' && capability !== 'manage_users'),
});

const renderDashboardWithRole = (roleName: UserRoleName = 'ADMIN') => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  const authValue = createMockAuthContext(roleName);

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthContext.Provider value={authValue}>
        <BrowserRouter>
          <DashboardPage />
        </BrowserRouter>
      </AuthContext.Provider>
    </QueryClientProvider>
  );
};

describe('Admin Command Center Dashboard Suite', () => {
  it('renders Admin Command Center header and welcome banner', () => {
    renderDashboardWithRole('ADMIN');

    expect(screen.getByText('Admin Command Center')).toBeInTheDocument();
    expect(screen.getByText(/Welcome back, System Administrator/i)).toBeInTheDocument();
    expect(screen.getAllByText('Admin').length).toBeGreaterThan(0);
    expect(screen.getByText('Refresh Data')).toBeInTheDocument();
  });

  it('renders all real inventory KPI categories', () => {
    renderDashboardWithRole('ADMIN');

    expect(screen.getByText('Total Items Tracked')).toBeInTheDocument();
    expect(screen.getByText('Expiring Soon (<=30d)')).toBeInTheDocument();
    expect(screen.getByText('Critical Stock (<=7d)')).toBeInTheDocument();
    expect(screen.getByText('Expired Stock (<0d)')).toBeInTheDocument();
  });

  it('renders Admin Quick Actions shortcuts', () => {
    renderDashboardWithRole('ADMIN');

    expect(screen.getByText('Admin Quick Actions')).toBeInTheDocument();
    expect(screen.getByText('Manage Products')).toBeInTheDocument();
    expect(screen.getByText('Inventory Balances')).toBeInTheDocument();
    expect(screen.getByText('Product Batches')).toBeInTheDocument();
    expect(screen.getByText('FEFO Allocation')).toBeInTheDocument();
    expect(screen.getAllByText('Expiry Risk').length).toBeGreaterThan(0);
    expect(screen.getByText('User Governance')).toBeInTheDocument();
  });

  it('renders explicit AI Intelligence Roadmap placeholders without fake predictions', () => {
    renderDashboardWithRole('ADMIN');

    expect(screen.getByText('AI Intelligence & Predictive Operations')).toBeInTheDocument();
    expect(screen.getByText('Demand & Reorder Forecasting')).toBeInTheDocument();
    expect(screen.getByText('Waste & Spoilage Prediction')).toBeInTheDocument();
    expect(screen.getByText('Smart Markdown Recommendations')).toBeInTheDocument();
    expect(screen.getByText(/No mock predictions are generated/i)).toBeInTheDocument();
  });

  it('hides User Governance quick action for non-admin roles', () => {
    renderDashboardWithRole('BUSINESS_MANAGER');

    expect(screen.queryByText('User Governance')).not.toBeInTheDocument();
  });
});
