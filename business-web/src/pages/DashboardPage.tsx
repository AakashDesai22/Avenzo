/**
 * AVENZO Business Web — Operational Dashboard / Admin Command Center
 * Central operational overview for the Avenzo Business Platform.
 * Powered strictly by real backend APIs with graceful loading, error handling, and role security.
 */

import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getExpirySummaryApi, getRiskMetricsApi } from '../api/expiry.api';
import { getMyNotificationsApi } from '../api/notifications.api';
import { Header } from '../components/layout/Header';
import { formatCurrency } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { getRoleDisplayLabel } from '../types/auth';
import { Link } from 'react-router-dom';
import {
  RefreshCw,
  ShieldCheck,
  Layers,
  AlertTriangle,
  Flame,
  AlertOctagon,
  TrendingDown,
  DollarSign,
  Package,
  Boxes,
  Award,
  Users,
  Bell,
  Sparkles,
  ArrowRight,
  Clock,
  AlertCircle,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user, can } = useAuth();
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const canViewFinancialRisk = can('view_financial_risk');
  const canManageUsers = can('manage_users');
  const roleLabel = getRoleDisplayLabel(user?.role?.name);

  // Queries for real API data
  const {
    data: summaryRes,
    isLoading: isSummaryLoading,
    isError: isSummaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['expirySummaryDashboard'],
    queryFn: () => getExpirySummaryApi(),
  });

  const {
    data: riskRes,
    isLoading: isRiskLoading,
    isError: isRiskError,
    refetch: refetchRisk,
  } = useQuery({
    queryKey: ['riskMetricsDashboard'],
    queryFn: () => getRiskMetricsApi(),
    enabled: canViewFinancialRisk,
  });

  const {
    data: notifRes,
    isLoading: isNotifLoading,
    isError: isNotifError,
    refetch: refetchNotif,
  } = useQuery({
    queryKey: ['notificationsDashboard'],
    queryFn: () => getMyNotificationsApi(false),
  });

  const summary = summaryRes?.data;
  const risk = riskRes?.data;
  const notifications = notifRes?.data?.slice(0, 5) || [];

  const handleRefreshAll = async () => {
    setIsRefreshing(true);
    await Promise.all([
      refetchSummary(),
      canViewFinancialRisk ? refetchRisk() : Promise.resolve(),
      refetchNotif(),
      queryClient.invalidateQueries({ queryKey: ['inventory'] }),
    ]);
    setLastUpdated(new Date());
    setIsRefreshing(false);
  };

  const kpis = [
    {
      title: 'Total Items Tracked',
      value: summary ? summary.total_items_tracked.toLocaleString() : '0',
      subtitle: `SAFE Stock: ${summary ? summary.safe_quantity.toLocaleString() : 0} units`,
      icon: Layers,
      color: '#2563eb',
      bgColor: '#eff6ff',
    },
    {
      title: 'Expiring Soon (<=30d)',
      value: summary ? summary.expiring_soon_quantity.toLocaleString() : '0',
      subtitle: `${summary ? summary.expiring_soon_batches_count : 0} active batches`,
      icon: AlertTriangle,
      color: '#d97706',
      bgColor: '#fefce8',
    },
    {
      title: 'Critical Stock (<=7d)',
      value: summary ? summary.critical_quantity.toLocaleString() : '0',
      subtitle: 'Immediate FEFO pick action required',
      icon: Flame,
      color: '#dc2626',
      bgColor: '#fff1f2',
    },
    {
      title: 'Expired Stock (<0d)',
      value: summary ? summary.expired_quantity.toLocaleString() : '0',
      subtitle: 'Quarantined for disposal',
      icon: AlertOctagon,
      color: '#991b1b',
      bgColor: '#fef2f2',
    },
  ];

  const quickActions = [
    { label: 'Manage Products', path: '/products', icon: Package, roles: ['ADMIN', 'BUSINESS_MANAGER'] },
    { label: 'Inventory Balances', path: '/inventory', icon: Layers, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    { label: 'Product Batches', path: '/batches', icon: Boxes, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    { label: 'FEFO Allocation', path: '/fefo', icon: Award, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    { label: 'Expiry Risk', path: '/risk', icon: TrendingDown, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    ...(canManageUsers
      ? [{ label: 'User Governance', path: '/users', icon: Users, roles: ['ADMIN'] }]
      : []),
    { label: 'System Notifications', path: '/notifications', icon: Bell, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Command Center Header */}
      <Header
        title="Admin Command Center"
        subtitle="Real-time Warehouse Operations & Inventory Expiry Governance"
        action={
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Clock size={14} />
              <span>Updated {lastUpdated.toLocaleTimeString()}</span>
            </div>
            <button
              onClick={handleRefreshAll}
              disabled={isRefreshing}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.5rem 1rem',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.375rem',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              <RefreshCw size={16} className={isRefreshing ? 'spin' : ''} />
              {isRefreshing ? 'Refreshing...' : 'Refresh Data'}
            </button>
          </div>
        }
      />

      {/* User Welcome & Governance Card */}
      <div
        style={{
          backgroundColor: '#0f172a',
          color: '#ffffff',
          padding: '1.5rem 2rem',
          borderRadius: '0.75rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#ffffff' }}>
              Welcome back, {user?.first_name} {user?.last_name}
            </h1>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '0.125rem 0.5rem',
                borderRadius: '0.25rem',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
              }}
            >
              <ShieldCheck size={12} />
              {roleLabel}
            </span>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: 0 }}>
            System operational status normal. FEFO pick rules active. Automated expiry monitoring online.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <Link
            to="/fefo"
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#1e293b',
              color: '#60a5fa',
              borderRadius: '0.375rem',
              textDecoration: 'none',
              fontWeight: 600,
              fontSize: '0.875rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.375rem',
              border: '1px solid #334155',
            }}
          >
            <Award size={16} /> FEFO Pick List
          </Link>
          <Link
            to="/risk"
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#1e293b',
              color: '#f87171',
              borderRadius: '0.375rem',
              textDecoration: 'none',
              fontWeight: 600,
              fontSize: '0.875rem',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.375rem',
              border: '1px solid #334155',
            }}
          >
            <TrendingDown size={16} /> Expiry Risk
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div
              key={idx}
              style={{
                backgroundColor: '#ffffff',
                padding: '1.25rem',
                borderRadius: '0.5rem',
                border: '1px solid #e2e8f0',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
              }}
            >
              <div>
                <span style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: 500 }}>{kpi.title}</span>
                <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a', margin: '0.25rem 0 0' }}>
                  {isSummaryLoading ? '...' : kpi.value}
                </h2>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>{kpi.subtitle}</p>
              </div>
              <div
                style={{
                  padding: '0.625rem',
                  borderRadius: '0.375rem',
                  backgroundColor: kpi.bgColor,
                  color: kpi.color,
                }}
              >
                <Icon size={22} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Financial Exposure & Stock Classification Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
        {/* Financial Risk Exposure */}
        {canViewFinancialRisk && (
          <div
            style={{
              backgroundColor: '#ffffff',
              padding: '1.5rem',
              borderRadius: '0.5rem',
              border: '1px solid #e2e8f0',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                    Financial Exposure at Risk
                  </h3>
                  <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0.125rem 0 0' }}>
                    Capital evaluated at Cost Price vs Potential Selling Value
                  </p>
                </div>
                <TrendingDown size={24} color="#dc2626" />
              </div>

              {isRiskError ? (
                <div style={{ padding: '1rem', backgroundColor: '#fef2f2', color: '#991b1b', borderRadius: '0.375rem', fontSize: '0.875rem' }}>
                  <AlertCircle size={16} style={{ display: 'inline', marginRight: '0.375rem' }} />
                  Failed to load financial risk metrics.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div style={{ padding: '0.75rem', borderRadius: '0.375rem', backgroundColor: '#fff1f2', color: '#dc2626' }}>
                      <TrendingDown size={24} />
                    </div>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Capital Exposure at Risk (Cost Price)</span>
                      <h4 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#dc2626', margin: 0 }}>
                        {isRiskLoading ? '...' : formatCurrency(risk?.capital_exposure_at_risk)}
                      </h4>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', borderTop: '1px solid #f1f5f9', paddingTop: '1rem' }}>
                    <div style={{ padding: '0.75rem', borderRadius: '0.375rem', backgroundColor: '#fefce8', color: '#d97706' }}>
                      <DollarSign size={24} />
                    </div>
                    <div>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Potential Revenue Exposure (Sales Price)</span>
                      <h4 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#d97706', margin: 0 }}>
                        {isRiskLoading ? '...' : formatCurrency(risk?.potential_sales_exposure)}
                      </h4>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div style={{ marginTop: '1.25rem', paddingTop: '0.875rem', borderTop: '1px solid #f1f5f9', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Expiry Exposure Ratio</span>
              <span style={{ fontSize: '1rem', fontWeight: 700, color: '#0f172a' }}>
                {isRiskLoading ? '...' : `${risk?.expiry_exposure_percentage || 0}%`}
              </span>
            </div>
          </div>
        )}

        {/* Stock Health Breakdown */}
        <div
          style={{
            backgroundColor: '#ffffff',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #e2e8f0',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: '0 0 0.25rem' }}>
              Stock Health Breakdown
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 1.25rem' }}>
              Real-time stock quantity distribution by FEFO expiry status
            </p>

            {isSummaryError ? (
              <div style={{ padding: '1rem', backgroundColor: '#fef2f2', color: '#991b1b', borderRadius: '0.375rem', fontSize: '0.875rem' }}>
                Failed to load stock summary.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.875rem', color: '#166534', fontWeight: 600 }}>SAFE Stock</span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0f172a' }}>
                    {isSummaryLoading ? '...' : `${summary?.safe_quantity.toLocaleString() || 0} units`}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.875rem', color: '#ca8a04', fontWeight: 600 }}>EXPIRING SOON (&lt;=30d)</span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0f172a' }}>
                    {isSummaryLoading ? '...' : `${summary?.expiring_soon_quantity.toLocaleString() || 0} units`}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.875rem', color: '#e11d48', fontWeight: 600 }}>CRITICAL STOCK (&lt;=7d)</span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0f172a' }}>
                    {isSummaryLoading ? '...' : `${summary?.critical_quantity.toLocaleString() || 0} units`}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.875rem', color: '#dc2626', fontWeight: 600 }}>EXPIRED STOCK</span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0f172a' }}>
                    {isSummaryLoading ? '...' : `${summary?.expired_quantity.toLocaleString() || 0} units`}
                  </span>
                </div>
              </div>
            )}
          </div>

          <div style={{ marginTop: '1.25rem', paddingTop: '0.875rem', borderTop: '1px solid #f1f5f9' }}>
            <Link
              to="/risk"
              style={{
                fontSize: '0.875rem',
                color: '#2563eb',
                fontWeight: 600,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
              }}
            >
              View Full Expiry Risk Analytics <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Actions & Notifications Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Quick Actions Grid */}
        <div
          style={{
            backgroundColor: '#ffffff',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #e2e8f0',
          }}
        >
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: '0 0 0.25rem' }}>
            Admin Quick Actions
          </h3>
          <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 1rem' }}>
            Operational shortcuts for system administration
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem' }}>
            {quickActions.map((act) => {
              const Icon = act.icon;
              return (
                <Link
                  key={act.path}
                  to={act.path}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '1rem 0.5rem',
                    backgroundColor: '#f8fafc',
                    borderRadius: '0.375rem',
                    border: '1px solid #e2e8f0',
                    textDecoration: 'none',
                    color: '#0f172a',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    textAlign: 'center',
                    gap: '0.5rem',
                    transition: 'background-color 0.15s ease',
                  }}
                >
                  <Icon size={20} color="#2563eb" />
                  {act.label}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Business Notifications Feed */}
        <div
          style={{
            backgroundColor: '#ffffff',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #e2e8f0',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                Recent Operational Alerts
              </h3>
              <Bell size={18} color="#64748b" />
            </div>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 1rem' }}>
              System warnings and automated expiry monitoring alerts
            </p>

            {isNotifLoading ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: '0.875rem' }}>
                Loading system alerts...
              </div>
            ) : isNotifError ? (
              <div style={{ padding: '1rem', backgroundColor: '#fef2f2', color: '#991b1b', borderRadius: '0.375rem', fontSize: '0.875rem' }}>
                Failed to retrieve notifications.
              </div>
            ) : notifications.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.875rem' }}>
                No active operational alerts.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {notifications.map((n) => (
                  <div
                    key={n.id}
                    style={{
                      padding: '0.75rem',
                      borderRadius: '0.375rem',
                      backgroundColor: n.is_read ? '#f8fafc' : '#eff6ff',
                      border: '1px solid #e2e8f0',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.625rem',
                    }}
                  >
                    <AlertTriangle size={16} color={n.notification_type.includes('EXPIRY') ? '#d97706' : '#2563eb'} style={{ marginTop: '0.125rem' }} />
                    <div style={{ overflow: 'hidden' }}>
                      <h5 style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#0f172a', margin: 0 }}>
                        {n.title}
                      </h5>
                      <p style={{ fontSize: '0.75rem', color: '#475569', margin: '0.125rem 0', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {n.body}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ marginTop: '1.25rem', paddingTop: '0.875rem', borderTop: '1px solid #f1f5f9' }}>
            <Link
              to="/notifications"
              style={{
                fontSize: '0.875rem',
                color: '#2563eb',
                fontWeight: 600,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
              }}
            >
              View All System Notifications <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </div>

      {/* AI Intelligence Roadmap Section (Explicit Placeholders) */}
      <div
        style={{
          backgroundColor: '#ffffff',
          padding: '1.5rem',
          borderRadius: '0.5rem',
          border: '1px solid #e2e8f0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <Sparkles size={20} color="#7c3aed" />
          <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
            AI Intelligence & Predictive Operations
          </h3>
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              padding: '0.125rem 0.5rem',
              borderRadius: '0.25rem',
              backgroundColor: '#f3e8ff',
              color: '#7c3aed',
              textTransform: 'uppercase',
            }}
          >
            Future AI Roadmap
          </span>
        </div>
        <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 1.25rem' }}>
          AI-driven forecasting and smart Markdown engines will be integrated in upcoming platform phases. No mock predictions are generated.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px border-dashed #cbd5e1' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7c3aed' }}>MODULE 01</span>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a', margin: '0.25rem 0' }}>
              Demand & Reorder Forecasting
            </h4>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>
              Predictive ML models analyzing historical velocity and seasonal demand. Coming in Phase 14.
            </p>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px border-dashed #cbd5e1' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7c3aed' }}>MODULE 02</span>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a', margin: '0.25rem 0' }}>
              Waste & Spoilage Prediction
            </h4>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>
              Automated expiry risk scoring based on ambient conditions and turnover rates. Coming in Phase 14.
            </p>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px border-dashed #cbd5e1' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7c3aed' }}>MODULE 03</span>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a', margin: '0.25rem 0' }}>
              Smart Markdown Recommendations
            </h4>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>
              Dynamic price reduction recommendations for near-expiry stock to maximize recovery. Coming in Phase 14.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
