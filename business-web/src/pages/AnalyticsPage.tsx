/**
 * AVENZO Business Web — Analyst Intelligence Workspace Page
 * Dedicated analytical dashboard for Analyst (STAFF) and Admin roles.
 * Provides deep-dive insights on inventory health, expiry exposure, waste/risk,
 * FEFO pick velocity, and AI forecasting readiness. Strictly read-only.
 */

import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { getExpirySummaryApi, getRiskMetricsApi } from '../api/expiry.api';
import { getBatchesApi, getInventoryApi, getWarehousesApi, getInventoryTransactionsApi } from '../api/inventory.api';
import { getBusinessWasteAnalyticsApi } from '../api/analytics.api';
import { formatCurrency, formatDate } from '../utils/formatters';
import { Header } from '../components/layout/Header';
import { Badge } from '../components/ui/Badge';
import { useAuth } from '../context/AuthContext';
import { getRoleDisplayLabel } from '../types/auth';
import { Link } from 'react-router-dom';
import {
  TrendingDown,
  DollarSign,
  PieChart,
  ShieldCheck,
  Clock,
  RefreshCw,
  Award,
  Sparkles,
  Layers,
  AlertTriangle,
  Building2,
  AlertCircle,
} from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [selectedWarehouse, setSelectedWarehouse] = useState<string>('');

  const roleLabel = getRoleDisplayLabel(user?.role?.name);

  // Queries for real API data
  const {
    data: summaryRes,
    isLoading: isSummaryLoading,
    isError: isSummaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['expirySummaryAnalytics'],
    queryFn: () => getExpirySummaryApi(),
  });

  const {
    data: riskRes,
    isLoading: isRiskLoading,
    isError: isRiskError,
    refetch: refetchRisk,
  } = useQuery({
    queryKey: ['riskMetricsAnalytics'],
    queryFn: () => getRiskMetricsApi(),
  });

  const {
    data: batchesRes,
    isLoading: isBatchesLoading,
    refetch: refetchBatches,
  } = useQuery({
    queryKey: ['batchesAnalytics'],
    queryFn: () => getBatchesApi(),
  });

  const {
    data: inventoryRes,
    isLoading: isInvLoading,
    refetch: refetchInv,
  } = useQuery({
    queryKey: ['inventoryAnalytics', selectedWarehouse],
    queryFn: () => getInventoryApi({ warehouse_id: selectedWarehouse || undefined }),
  });

  const { data: warehousesRes } = useQuery({
    queryKey: ['warehousesAnalytics'],
    queryFn: () => getWarehousesApi(),
  });

  const { data: txRes } = useQuery({
    queryKey: ['fefoViolationsAnalytics'],
    queryFn: () => getInventoryTransactionsApi({ limit: 50 }),
  });

  const {
    data: wasteAnalyticsRes,
    isLoading: isWasteLoading,
    refetch: refetchWaste,
  } = useQuery({
    queryKey: ['businessWasteAnalytics'],
    queryFn: () => getBusinessWasteAnalyticsApi(),
  });

  const summary = summaryRes?.data;
  const risk = riskRes?.data;
  const batches = batchesRes?.data || [];
  const inventoryList = inventoryRes?.data || [];
  const wasteAnalytics = wasteAnalyticsRes?.data;
  const violations = (txRes?.data || []).filter((t) => t.transaction_type === 'FEFO_VIOLATION');

  const handleRefreshAll = async () => {
    setIsRefreshing(true);
    await Promise.all([
      refetchSummary(),
      refetchRisk(),
      refetchBatches(),
      refetchInv(),
      refetchWaste(),
      queryClient.invalidateQueries({ queryKey: ['batches'] }),
    ]);
    setLastUpdated(new Date());
    setIsRefreshing(false);
  };

  const totalTrackedUnits = summary?.total_items_tracked || 1;
  const safePct = summary ? Math.round((summary.safe_quantity / totalTrackedUnits) * 100) : 0;
  const expiringPct = summary ? Math.round((summary.expiring_soon_quantity / totalTrackedUnits) * 100) : 0;
  const criticalPct = summary ? Math.round((summary.critical_quantity / totalTrackedUnits) * 100) : 0;
  const expiredPct = summary ? Math.round((summary.expired_quantity / totalTrackedUnits) * 100) : 0;

  const getDteStatus = (expDate?: string) => {
    if (!expDate) return 'SAFE';
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const exp = new Date(expDate);
    exp.setHours(0, 0, 0, 0);
    const diffDays = Math.ceil((exp.getTime() - today.getTime()) / (1000 * 3600 * 24));
    if (diffDays < 0) return 'EXPIRED';
    if (diffDays <= 7) return 'CRITICAL';
    if (diffDays <= 30) return 'EXPIRING_SOON';
    return 'SAFE';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Analyst Header */}
      <Header
        title="Analyst Intelligence Workspace"
        subtitle="Operational inventory health, financial exposure, FEFO compliance, and forecasting readiness"
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
              {isRefreshing ? 'Refreshing...' : 'Refresh Analytics'}
            </button>
          </div>
        }
      />

      {/* Analyst Overview Banner */}
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
              Analytical Operational Overview
            </h1>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '0.125rem 0.5rem',
                borderRadius: '0.25rem',
                backgroundColor: '#7c3aed',
                color: '#ffffff',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
              }}
            >
              <ShieldCheck size={12} />
              {roleLabel} (Read-Only)
            </span>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: 0 }}>
            Read-only evaluation of warehouse inventory turnover, capital exposure risk, and FEFO picking compliance.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
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
            <Award size={16} /> FEFO Analytics
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
            <TrendingDown size={16} /> Risk Breakdown
          </Link>
        </div>
      </div>

      {/* Financial Exposure & Risk Analytics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
        <div
          style={{
            backgroundColor: '#ffffff',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: 500 }}>Capital Exposure at Risk</span>
            <TrendingDown size={22} color="#dc2626" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#dc2626', margin: '0.5rem 0 0' }}>
            {isRiskLoading ? '...' : formatCurrency(risk?.capital_exposure_at_risk)}
          </h2>
          <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.375rem', lineHeight: 1.4 }}>
            <strong>Business Meaning:</strong> Estimated cost price of inventory near or past expiry. Represents direct capital loss if unrotated.
          </p>
        </div>

        <div
          style={{
            backgroundColor: '#ffffff',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: 500 }}>Potential Sales Revenue Exposure</span>
            <DollarSign size={22} color="#d97706" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#d97706', margin: '0.5rem 0 0' }}>
            {isRiskLoading ? '...' : formatCurrency(risk?.potential_sales_exposure)}
          </h2>
          <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.375rem', lineHeight: 1.4 }}>
            <strong>Business Meaning:</strong> Maximum gross retail revenue at risk of being lost if near-expiry stock expires unsold.
          </p>
        </div>

        <div
          style={{
            backgroundColor: '#ffffff',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: 500 }}>Expiry Exposure Ratio</span>
            <PieChart size={22} color="#2563eb" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a', margin: '0.5rem 0 0' }}>
            {isRiskLoading ? '...' : `${risk?.expiry_exposure_percentage || 0}%`}
          </h2>
          <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.375rem', lineHeight: 1.4 }}>
            <strong>Business Meaning:</strong> Percentage of total warehouse stock value categorized under near-expiry or expired status.
          </p>
        </div>
      </div>

      {/* Stock Classification Analytics & Progress Bars */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '0.5rem',
          border: '1px solid #e2e8f0',
          padding: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Inventory Health & Expiry Classification Breakdown
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0.125rem 0 0' }}>
              Distribution of tracked stock units across FEFO expiry boundaries
            </p>
          </div>
          <Layers size={22} color="#2563eb" />
        </div>

        {isSummaryError ? (
          <div style={{ padding: '1rem', backgroundColor: '#fef2f2', color: '#991b1b', borderRadius: '0.375rem', fontSize: '0.875rem' }}>
            <AlertCircle size={16} style={{ display: 'inline', marginRight: '0.375rem' }} />
            Failed to load stock classification data.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            <div style={{ padding: '1rem', borderRadius: '0.375rem', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: '#166534', fontWeight: 700 }}>SAFE STOCK (&gt;30d)</span>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#166534' }}>{safePct}%</span>
              </div>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#15803d', margin: '0.25rem 0 0' }}>
                {isSummaryLoading ? '...' : `${summary?.safe_quantity.toLocaleString() || 0} units`}
              </p>
              <div style={{ width: '100%', height: '6px', backgroundColor: '#dcfce7', borderRadius: '3px', marginTop: '0.5rem', overflow: 'hidden' }}>
                <div style={{ width: `${safePct}%`, height: '100%', backgroundColor: '#16a34a' }} />
              </div>
            </div>

            <div style={{ padding: '1rem', borderRadius: '0.375rem', backgroundColor: '#fefce8', border: '1px solid #fef08a' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: '#854d0e', fontWeight: 700 }}>EXPIRING SOON (&lt;=30d)</span>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#854d0e' }}>{expiringPct}%</span>
              </div>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ca8a04', margin: '0.25rem 0 0' }}>
                {isSummaryLoading ? '...' : `${summary?.expiring_soon_quantity.toLocaleString() || 0} units`}
              </p>
              <div style={{ width: '100%', height: '6px', backgroundColor: '#fef9c3', borderRadius: '3px', marginTop: '0.5rem', overflow: 'hidden' }}>
                <div style={{ width: `${expiringPct}%`, height: '100%', backgroundColor: '#ca8a04' }} />
              </div>
            </div>

            <div style={{ padding: '1rem', borderRadius: '0.375rem', backgroundColor: '#fff1f2', border: '1px solid #fecdd3' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: '#9f1239', fontWeight: 700 }}>CRITICAL STOCK (&lt;=7d)</span>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#9f1239' }}>{criticalPct}%</span>
              </div>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#e11d48', margin: '0.25rem 0 0' }}>
                {isSummaryLoading ? '...' : `${summary?.critical_quantity.toLocaleString() || 0} units`}
              </p>
              <div style={{ width: '100%', height: '6px', backgroundColor: '#ffe4e6', borderRadius: '3px', marginTop: '0.5rem', overflow: 'hidden' }}>
                <div style={{ width: `${criticalPct}%`, height: '100%', backgroundColor: '#e11d48' }} />
              </div>
            </div>

            <div style={{ padding: '1rem', borderRadius: '0.375rem', backgroundColor: '#fef2f2', border: '1px solid #fee2e2' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: '#991b1b', fontWeight: 700 }}>EXPIRED STOCK (&lt;0d)</span>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#991b1b' }}>{expiredPct}%</span>
              </div>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#dc2626', margin: '0.25rem 0 0' }}>
                {isSummaryLoading ? '...' : `${summary?.expired_quantity.toLocaleString() || 0} units`}
              </p>
              <div style={{ width: '100%', height: '6px', backgroundColor: '#fee2e2', borderRadius: '3px', marginTop: '0.5rem', overflow: 'hidden' }}>
                <div style={{ width: `${expiredPct}%`, height: '100%', backgroundColor: '#dc2626' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Closed-Loop Waste Intelligence & Consumer Utilization */}
      <div
        style={{
          backgroundColor: '#ffffff',
          padding: '1.5rem',
          borderRadius: '0.5rem',
          border: '1px solid #e2e8f0',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <PieChart size={20} color="#2563eb" /> Closed-Loop Consumer Waste & Utilization Analytics
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0.125rem 0 0' }}>
              Privacy-safe aggregate metrics derived from post-delivery consumer pantry audit logs
            </p>
          </div>
        </div>

        {isWasteLoading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: '0.875rem' }}>
            Loading closed-loop utilization metrics...
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Warehouse Expired Loss</span>
              <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#dc2626', margin: '0.25rem 0 0' }}>
                {formatCurrency(wasteAnalytics?.total_capital_lost_expired)}
              </p>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                {wasteAnalytics?.total_warehouse_expired_units || 0} units at cost
              </span>
            </div>

            <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Consumer Reported Discards</span>
              <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#d97706', margin: '0.25rem 0 0' }}>
                {wasteAnalytics?.total_consumer_reported_discards || 0} units
              </p>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Post-delivery consumer waste</span>
            </div>

            <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Consumer Utilized Volume</span>
              <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#16a34a', margin: '0.25rem 0 0' }}>
                {wasteAnalytics?.total_consumer_reported_consumptions || 0} units
              </p>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Successfully consumed</span>
            </div>

            <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px solid #cbd5e1' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748b' }}>Inventory Waste Ratio</span>
              <p style={{ fontSize: '1.5rem', fontWeight: 700, color: '#2563eb', margin: '0.25rem 0 0' }}>
                {wasteAnalytics?.overall_inventory_waste_percentage || 0}%
              </p>
              <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Warehouse spoilage rate</span>
            </div>
          </div>
        )}
      </div>

      {/* FEFO Rotation & Pick Velocity Analytics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {/* Highest Priority FEFO Pick Batches */}
        <div
          style={{
            backgroundColor: '#ffffff',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              FEFO Pick Sequence Analytics
            </h3>
            <Award size={20} color="#2563eb" />
          </div>
          <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 1rem' }}>
            Backend FEFO ranking algorithm: batches sorted strictly by earliest expiry date to prevent spoilage
          </p>

          {isBatchesLoading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b', fontSize: '0.875rem' }}>
              Evaluating FEFO picking sequence...
            </div>
          ) : batches.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8', fontSize: '0.875rem' }}>
              No active batches registered for FEFO picking.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              {batches.slice(0, 4).map((b, idx) => {
                const status = getDteStatus(b.expiry_date);
                return (
                  <div
                    key={b.id}
                    style={{
                      padding: '0.75rem',
                      borderRadius: '0.375rem',
                      backgroundColor: idx === 0 ? '#eff6ff' : '#f8fafc',
                      border: '1px solid #e2e8f0',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#2563eb' }}>#{idx + 1}</span>
                        <h4 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
                          {b.product?.name || 'Product'}
                        </h4>
                      </div>
                      <span style={{ fontSize: '0.75rem', color: '#64748b' }}>
                        Batch: <strong>{b.batch_number}</strong> | Exp: {formatDate(b.expiry_date)}
                      </span>
                    </div>
                    <Badge status={status} />
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* FEFO Violation & Rotation Audit Log */}
        <div
          style={{
            backgroundColor: '#ffffff',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Rotation & Pick Violation Audit
            </h3>
            <AlertTriangle size={20} color="#d97706" />
          </div>
          <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 1rem' }}>
            Audit log of pick overrides where a later-expiring batch was selected over an earlier-expiring batch
          </p>

          {violations.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: '#166534', backgroundColor: '#f0fdf4', borderRadius: '0.375rem', fontSize: '0.875rem' }}>
              <ShieldCheck size={24} style={{ display: 'block', margin: '0 auto 0.5rem', color: '#16a34a' }} />
              100% FEFO Pick Compliance. Zero audit violations detected.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              {violations.slice(0, 4).map((v) => (
                <div key={v.id} style={{ padding: '0.75rem', backgroundColor: '#fefce8', borderRadius: '0.375rem', border: '1px solid #fef08a' }}>
                  <Badge variant="warning">FEFO VIOLATION</Badge>
                  <p style={{ fontSize: '0.75rem', color: '#854d0e', margin: '0.25rem 0 0' }}>{v.notes}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Analytical Warehouse Filter Table */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '0.5rem',
          border: '1px solid #e2e8f0',
          padding: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Analytical Facility Inventory Breakdown
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0.125rem 0 0' }}>
              Inspect live stock balances by warehouse facility and location bin
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Building2 size={16} color="#64748b" />
            <select
              value={selectedWarehouse}
              onChange={(e) => setSelectedWarehouse(e.target.value)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#ffffff',
                border: '1px solid #cbd5e1',
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                color: '#0f172a',
              }}
            >
              <option value="">All Warehouses</option>
              {warehousesRes?.data?.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {isInvLoading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading facility stock balances...</div>
        ) : inventoryList.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>No stock balances found.</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', textAlign: 'left' }}>
                  <th style={{ padding: '0.75rem' }}>Product</th>
                  <th style={{ padding: '0.75rem' }}>SKU</th>
                  <th style={{ padding: '0.75rem' }}>Batch Number</th>
                  <th style={{ padding: '0.75rem' }}>Expiry Date</th>
                  <th style={{ padding: '0.75rem' }}>Facility</th>
                  <th style={{ padding: '0.75rem' }}>Bin</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right' }}>On Hand</th>
                  <th style={{ padding: '0.75rem', textAlign: 'right' }}>Available</th>
                </tr>
              </thead>
              <tbody>
                {inventoryList.slice(0, 8).map((inv) => (
                  <tr key={inv.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 600 }}>{inv.product?.name}</td>
                    <td style={{ padding: '0.75rem', color: '#64748b' }}>{inv.product?.sku}</td>
                    <td style={{ padding: '0.75rem' }}>{inv.batch?.batch_number}</td>
                    <td style={{ padding: '0.75rem' }}>{formatDate(inv.batch?.expiry_date)}</td>
                    <td style={{ padding: '0.75rem' }}>{inv.warehouse?.name}</td>
                    <td style={{ padding: '0.75rem' }}>
                      <span style={{ fontSize: '0.75rem', padding: '0.125rem 0.375rem', backgroundColor: '#f1f5f9', borderRadius: '0.25rem' }}>
                        {inv.location?.location_code || 'Default'}
                      </span>
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right' }}>{inv.quantity_on_hand.toLocaleString()}</td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 700, color: '#2563eb' }}>
                      {inv.quantity_available.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* AI & Forecasting Roadmap Section (Explicit Roadmap Placeholders) */}
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
            AI & Forecasting — Coming Next
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
            Future Roadmap
          </span>
        </div>
        <p style={{ fontSize: '0.75rem', color: '#64748b', margin: '0 0 1.25rem' }}>
          Planned predictive ML capabilities. No fake predictions or mock confidence scores are generated.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem' }}>
          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px border-dashed #cbd5e1' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7c3aed' }}>ROADMAP ITEM 01</span>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a', margin: '0.25rem 0' }}>
              Demand & Velocity Forecasting
            </h4>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>
              Historical sales velocity and reorder point predictions. Planned for Phase 14 AI Engine.
            </p>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px border-dashed #cbd5e1' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7c3aed' }}>ROADMAP ITEM 02</span>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a', margin: '0.25rem 0' }}>
              Spoilage & Waste Prediction
            </h4>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>
              Predictive risk scoring for perishable products based on turnover rate. Planned for Phase 14 AI Engine.
            </p>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#f8fafc', borderRadius: '0.375rem', border: '1px border-dashed #cbd5e1' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#7c3aed' }}>ROADMAP ITEM 03</span>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
              Smart Markdown Recommendations
            </h4>
            <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>
              Dynamic discount suggestions for near-expiry inventory to accelerate turnover. Planned for Phase 14.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
