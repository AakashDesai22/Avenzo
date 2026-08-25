/**
 * AVENZO Business Web — Analytics & Waste Forecasting Page (Analyst & Admin)
 * Displays business analytics, inventory risk breakdown, and capital exposure.
 */

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getExpirySummaryApi, getRiskMetricsApi } from '../api/expiry.api';
import { formatCurrency } from '../utils/formatters';
import { TrendingDown, DollarSign, PieChart } from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['expirySummaryAnalytics'],
    queryFn: () => getExpirySummaryApi(),
  });

  const { data: riskRes, isLoading: isRiskLoading } = useQuery({
    queryKey: ['riskMetricsAnalytics'],
    queryFn: () => getRiskMetricsApi(),
  });

  const summary = summaryRes?.data;
  const risk = riskRes?.data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
          Inventory Analytics & Waste Forecasting
        </h1>
        <p style={{ fontSize: '0.875rem', color: '#64748b', margin: '0.25rem 0 0' }}>
          Deep-dive analysis of capital exposure, near-expiry financial risk, and stock distribution.
        </p>
      </div>

      {/* Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
        <div
          style={{
            backgroundColor: '#ffffff',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            border: '1px solid #e2e8f0',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: 500 }}>Capital Exposure (Cost)</span>
            <TrendingDown size={20} color="#dc2626" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#dc2626', margin: '0.5rem 0 0' }}>
            {isRiskLoading ? '...' : formatCurrency(risk?.capital_exposure_at_risk)}
          </h2>
          <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
            Total stock cost at risk of expiring within 30 days
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
            <span style={{ fontSize: '0.875rem', color: '#64748b', fontWeight: 500 }}>Potential Revenue Exposure</span>
            <DollarSign size={20} color="#d97706" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#d97706', margin: '0.5rem 0 0' }}>
            {isRiskLoading ? '...' : formatCurrency(risk?.potential_sales_exposure)}
          </h2>
          <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
            Retail sales value of stock near expiry
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
            <PieChart size={20} color="#2563eb" />
          </div>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: '#0f172a', margin: '0.5rem 0 0' }}>
            {risk ? `${risk.expiry_exposure_percentage}%` : '0%'}
          </h2>
          <p style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.25rem' }}>
            Ratio of at-risk stock vs total tracked inventory
          </p>
        </div>
      </div>

      {/* Stock Classification Summary */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '0.5rem',
          border: '1px solid #e2e8f0',
          padding: '1.5rem',
        }}
      >
        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: '0 0 1rem' }}>
          Inventory Stock Classification Breakdown
        </h3>

        {isSummaryLoading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading analytics data...</div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div style={{ padding: '1rem', borderRadius: '0.375rem', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0' }}>
              <span style={{ fontSize: '0.75rem', color: '#166534', fontWeight: 600 }}>SAFE STOCK</span>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#15803d', margin: '0.25rem 0 0' }}>
                {summary?.safe_quantity.toLocaleString()} units
              </p>
            </div>

            <div style={{ padding: '1rem', borderRadius: '0.375rem', backgroundColor: '#fefce8', border: '1px solid #fef08a' }}>
              <span style={{ fontSize: '0.75rem', color: '#854d0e', fontWeight: 600 }}>EXPIRING SOON (&lt;=30d)</span>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ca8a04', margin: '0.25rem 0 0' }}>
                {summary?.expiring_soon_quantity.toLocaleString()} units
              </p>
            </div>

            <div style={{ padding: '1rem', borderRadius: '0.375rem', backgroundColor: '#fff1f2', border: '1px solid #fecdd3' }}>
              <span style={{ fontSize: '0.75rem', color: '#9f1239', fontWeight: 600 }}>CRITICAL STOCK (&lt;=7d)</span>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#e11d48', margin: '0.25rem 0 0' }}>
                {summary?.critical_quantity.toLocaleString()} units
              </p>
            </div>

            <div style={{ padding: '1rem', borderRadius: '0.375rem', backgroundColor: '#fef2f2', border: '1px solid #fee2e2' }}>
              <span style={{ fontSize: '0.75rem', color: '#991b1b', fontWeight: 600 }}>EXPIRED STOCK</span>
              <p style={{ fontSize: '1.25rem', fontWeight: 700, color: '#dc2626', margin: '0.25rem 0 0' }}>
                {summary?.expired_quantity.toLocaleString()} units
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
