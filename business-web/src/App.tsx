import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { RoleGuard } from './features/auth/RoleGuard';
import { Layout } from './components/layout/Layout';

import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { OrdersPage } from './pages/OrdersPage';
import { ProductsPage } from './pages/ProductsPage';
import { CategoriesPage } from './pages/CategoriesPage';
import { InventoryPage } from './pages/InventoryPage';
import { BatchesPage } from './pages/BatchesPage';
import { WarehousesPage } from './pages/WarehousesPage';
import { FefoPage } from './pages/FefoPage';
import { RiskPage } from './pages/RiskPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { UsersPage } from './pages/UsersPage';
import { NotificationsPage } from './pages/NotificationsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60 * 5, // 5 minutes stale time
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />

            <Route
              path="/"
              element={
                <RoleGuard allowedRoles={['ADMIN', 'BUSINESS_MANAGER', 'STAFF']}>
                  <Layout />
                </RoleGuard>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="orders" element={<OrdersPage />} />
              
              <Route
                path="products"
                element={
                  <RoleGuard allowedRoles={['ADMIN', 'BUSINESS_MANAGER']}>
                    <ProductsPage />
                  </RoleGuard>
                }
              />
              
              <Route
                path="categories"
                element={
                  <RoleGuard allowedRoles={['ADMIN', 'BUSINESS_MANAGER']}>
                    <CategoriesPage />
                  </RoleGuard>
                }
              />
              
              <Route path="inventory" element={<InventoryPage />} />
              <Route path="batches" element={<BatchesPage />} />
              <Route path="warehouses" element={<WarehousesPage />} />
              <Route path="fefo" element={<FefoPage />} />
              <Route path="risk" element={<RiskPage />} />
              
              <Route
                path="analytics"
                element={
                  <RoleGuard allowedRoles={['ADMIN', 'STAFF']}>
                    <AnalyticsPage />
                  </RoleGuard>
                }
              />

              <Route
                path="users"
                element={
                  <RoleGuard allowedRoles={['ADMIN']}>
                    <UsersPage />
                  </RoleGuard>
                }
              />

              <Route path="notifications" element={<NotificationsPage />} />
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
