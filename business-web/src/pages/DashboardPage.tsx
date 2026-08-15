import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getExpirySummaryApi, getRiskMetricsApi } from '../api/expiry.api';
import { Header } from '../components/layout/Header';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { formatCurrency } from '../utils/formatters';
import { Layers, AlertTriangle, Flame, AlertOctagon, TrendingDown, DollarSign } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { data: summaryRes, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['expirySummary'],
    queryFn: () => getExpirySummaryApi(),
  });

  const { data: riskRes, isLoading: isRiskLoading } = useQuery({
    queryKey: ['riskMetrics'],
    queryFn: () => getRiskMetricsApi(),
  });

  const summary = summaryRes?.data;
  const risk = riskRes?.data;

  const kpis = [
    {
      title: 'Total Items Tracked',
      value: summary ? summary.total_items_tracked.toLocaleString() : '0',
      subtitle: `SAFE Stock: ${summary ? summary.safe_quantity.toLocaleString() : 0} units`,
      icon: Layers,
      color: 'var(--color-primary)',
    },
    {
      title: 'Expiring Soon (<=30d)',
      value: summary ? summary.expiring_soon_quantity.toLocaleString() : '0',
      subtitle: `${summary ? summary.expiring_soon_batches_count : 0} active batches`,
      icon: AlertTriangle,
      color: 'var(--color-warning)',
    },
    {
      title: 'Critical Stock (<=7d)',
      value: summary ? summary.critical_quantity.toLocaleString() : '0',
      subtitle: 'Immediate FEFO action required',
      icon: Flame,
      color: 'var(--color-danger)',
    },
    {
      title: 'Expired Stock (<0d)',
      value: summary ? summary.expired_quantity.toLocaleString() : '0',
      subtitle: 'Quarantined for disposal',
      icon: AlertOctagon,
      color: '#fca5a5',
    },
  ];

  return (
    <div>
      <Header
        title="Operational Dashboard"
        subtitle="Real-time Inventory Intelligence & Expiry Overview"
      />

      <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* KPI Cards Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
          {kpis.map((kpi, idx) => {
            const Icon = kpi.icon;
            return (
              <Card key={idx}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>{kpi.title}</span>
                    <h2 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-text-primary)', marginTop: '0.25rem' }}>
                      {isSummaryLoading ? '...' : kpi.value}
                    </h2>
                    <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                      {kpi.subtitle}
                    </p>
                  </div>
                  <div
                    style={{
                      padding: '0.625rem',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--color-border-subtle)',
                      color: kpi.color,
                    }}
                  >
                    <Icon size={22} />
                  </div>
                </div>
              </Card>
            );
          })}
        </div>

        {/* Financial Risk & Capital Exposure Widgets */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '1.25rem' }}>
          <Card title="Capital Exposure at Risk" subtitle="Financial inventory value near expiry evaluated at Cost Price vs Sales Price">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginTop: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger)' }}>
                  <TrendingDown size={28} />
                </div>
                <div>
                  <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>Capital Exposure at Risk (Cost Price)</span>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-danger)' }}>
                    {isRiskLoading ? '...' : formatCurrency(risk?.capital_exposure_at_risk)}
                  </h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    Total stock near expiry or expired evaluated at cost
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
                <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-warning-bg)', color: 'var(--color-warning)' }}>
                  <DollarSign size={28} />
                </div>
                <div>
                  <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>Potential Sales Revenue at Risk (Unit Price)</span>
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-warning)' }}>
                    {isRiskLoading ? '...' : formatCurrency(risk?.potential_sales_exposure)}
                  </h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    Potential sales value if stock expires unsold
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-border-subtle)', fontSize: '0.875rem' }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>Expiry Exposure Ratio</span>
                <span style={{ fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  {risk ? `${risk.expiry_exposure_percentage}%` : '0%'}
                </span>
              </div>
            </div>
          </Card>

          <Card title="Stock Status Breakdown" subtitle="Distribution across Expiry Classifications">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Badge status="SAFE" />
                <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {summary ? summary.safe_quantity.toLocaleString() : 0} units
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Badge status="EXPIRING_SOON" />
                <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {summary ? summary.expiring_soon_quantity.toLocaleString() : 0} units
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Badge status="CRITICAL" />
                <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {summary ? summary.critical_quantity.toLocaleString() : 0} units
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Badge status="EXPIRED" />
                <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {summary ? summary.expired_quantity.toLocaleString() : 0} units
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Badge status="N/A" />
                <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                  {summary ? summary.non_expiry_quantity.toLocaleString() : 0} units
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
