import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRiskMetricsApi } from '../api/expiry.api';
import { Header } from '../components/layout/Header';
import { Card } from '../components/ui/Card';
import { formatCurrency } from '../utils/formatters';
import { ShieldAlert, TrendingDown, DollarSign, Percent, AlertOctagon } from 'lucide-react';

export const RiskPage: React.FC = () => {
  const { data: riskRes, isLoading } = useQuery({
    queryKey: ['riskMetrics'],
    queryFn: () => getRiskMetricsApi(),
  });

  const risk = riskRes?.data;

  return (
    <div>
      <Header
        title="Inventory Risk & Financial Exposure"
        subtitle="Deterministic rule-based risk metrics and capital exposure analysis"
      />

      <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Top Risk Exposure Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          <Card title="Capital Exposure at Risk">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.5rem' }}>
              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger)' }}>
                <TrendingDown size={28} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-danger)' }}>
                  {isLoading ? '...' : formatCurrency(risk?.capital_exposure_at_risk)}
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                  Calculated at Cost Price (Product Cost Exposure)
                </span>
              </div>
            </div>
          </Card>

          <Card title="Potential Sales Revenue Exposure">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.5rem' }}>
              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-warning-bg)', color: 'var(--color-warning)' }}>
                <DollarSign size={28} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-warning)' }}>
                  {isLoading ? '...' : formatCurrency(risk?.potential_sales_exposure)}
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                  Calculated at Selling Unit Price
                </span>
              </div>
            </div>
          </Card>

          <Card title="Expiry Exposure Percentage">
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.5rem' }}>
              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--color-neutral-bg)', color: 'var(--color-primary)' }}>
                <Percent size={28} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--color-primary)' }}>
                  {isLoading ? '...' : `${risk?.expiry_exposure_percentage || 0}%`}
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                  Ratio of Near-Expiry + Expired stock to Total Stock
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Detailed Risk Breakdown Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          <Card title="Near-Expiry Stock (<=30 Days)" subtitle="Inventory approaching expiration deadline">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <ShieldAlert size={24} color="var(--color-warning)" />
                <span style={{ fontSize: '1.25rem', fontWeight: 600 }}>{risk?.near_expiry_quantity.toLocaleString() || 0} Units</span>
              </div>
              <span style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>Prioritize in FEFO</span>
            </div>
          </Card>

          <Card title="Critical Expiry Stock (<=7 Days)" subtitle="High risk of loss within 1 week">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <ShieldAlert size={24} color="var(--color-danger)" />
                <span style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--color-danger)' }}>{risk?.critical_expiry_quantity.toLocaleString() || 0} Units</span>
              </div>
              <span style={{ fontSize: '0.875rem', color: 'var(--color-danger)' }}>Immediate Action Required</span>
            </div>
          </Card>

          <Card title="Expired Stock (<0 Days)" subtitle="Total dead stock requiring write-off">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <AlertOctagon size={24} color="#fca5a5" />
                <span style={{ fontSize: '1.25rem', fontWeight: 600, color: '#fca5a5' }}>{risk?.expired_quantity.toLocaleString() || 0} Units</span>
              </div>
              <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Quarantined</span>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
