import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getFefoBatchesApi, previewFefoAllocationApi, verifyFefoSelectionApi } from '../api/fefo.api';
import { getProductsApi } from '../api/products.api';
import { FEFORankedBatch, FEFOAllocationPlan, FEFOVerificationResponse } from '../types/fefo';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { formatDate } from '../utils/formatters';
import { Award, AlertTriangle, CheckCircle } from 'lucide-react';

export const FefoPage: React.FC = () => {
  const [selectedProductId, setSelectedProductId] = useState<string>('');

  // Allocation Preview Modal State
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [reqProduct, setReqProduct] = useState('');
  const [reqQuantity, setReqQuantity] = useState('50');
  const [allocationPlan, setAllocationPlan] = useState<FEFOAllocationPlan | null>(null);

  // Verification Modal State
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [verProduct, setVerProduct] = useState('');
  const [verBatchId, setVerBatchId] = useState('');
  const [verQuantity, setVerQuantity] = useState('20');
  const [verReason, setVerReason] = useState('');
  const [verificationResult, setVerificationResult] = useState<FEFOVerificationResponse | null>(null);

  const { data: productsRes } = useQuery({
    queryKey: ['productsAll'],
    queryFn: () => getProductsApi({ limit: 100 }),
  });

  const { data: fefoBatchesRes, isLoading: isFefoLoading } = useQuery({
    queryKey: ['fefoBatches', selectedProductId],
    queryFn: () => getFefoBatchesApi(selectedProductId),
    enabled: !!selectedProductId,
  });

  const previewMutation = useMutation({
    mutationFn: (data: { product_id: string; requested_quantity: number }) => previewFefoAllocationApi(data),
    onSuccess: (res) => {
      if (res.success && res.data) {
        setAllocationPlan(res.data);
      }
    },
  });

  const verifyMutation = useMutation({
    mutationFn: (data: { product_id: string; selected_batch_id: string; requested_quantity: number; override_reason?: string }) =>
      verifyFefoSelectionApi(data),
    onSuccess: (res) => {
      if (res.success && res.data) {
        setVerificationResult(res.data);
      }
    },
  });

  const handleGeneratePreview = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reqProduct || !reqQuantity) return;
    previewMutation.mutate({ product_id: reqProduct, requested_quantity: parseInt(reqQuantity, 10) });
  };

  const handleVerifySelection = (e: React.FormEvent) => {
    e.preventDefault();
    if (!verProduct || !verBatchId || !verQuantity) return;
    verifyMutation.mutate({
      product_id: verProduct,
      selected_batch_id: verBatchId,
      requested_quantity: parseInt(verQuantity, 10),
      override_reason: verReason || undefined,
    });
  };

  const columns: Column<FEFORankedBatch>[] = [
    {
      key: 'fefo_rank',
      header: 'FEFO Rank',
      render: (b) => (
        <span style={{ fontWeight: 700, color: b.fefo_rank === 1 ? 'var(--color-primary)' : 'var(--color-text-primary)' }}>
          #{b.fefo_rank}
        </span>
      ),
    },
    { key: 'product_name', header: 'Product', render: (b) => b.product_name },
    { key: 'sku', header: 'SKU', render: (b) => b.sku },
    { key: 'batch_number', header: 'Batch Number', render: (b) => <span style={{ fontWeight: 600 }}>{b.batch_number}</span> },
    { key: 'warehouse_name', header: 'Warehouse', render: (b) => b.warehouse_name },
    { key: 'location_code', header: 'Location', render: (b) => b.location_code || 'Unassigned' },
    { key: 'expiry_date', header: 'Expiry Date', render: (b) => formatDate(b.expiry_date) },
    { key: 'days_to_expiry', header: 'Days Left', render: (b) => (b.days_to_expiry !== undefined ? `${b.days_to_expiry} days` : 'N/A') },
    { key: 'expiry_status', header: 'Status', render: (b) => <Badge status={b.expiry_status} /> },
    {
      key: 'quantity_available',
      header: 'Available Stock',
      render: (b) => <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{b.quantity_available.toLocaleString()}</span>,
    },
  ];

  return (
    <div>
      <Header
        title="FEFO Intelligence Engine"
        subtitle="First-Expired, First-Out pick list ranking, non-mutating allocation preview, & violation audits"
        action={
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Button variant="outline" onClick={() => setIsVerifyModalOpen(true)}>
              Verify Batch Pick Selection
            </Button>
            <Button onClick={() => setIsPreviewModalOpen(true)}>
              <Award size={18} /> Allocation Preview
            </Button>
          </div>
        }
      />

      <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Product Selector Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <label style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>Select Product for FEFO Ranking:</label>
          <select
            value={selectedProductId}
            onChange={(e) => setSelectedProductId(e.target.value)}
            style={{
              padding: '0.625rem 1rem',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-primary)',
              minWidth: '280px',
            }}
          >
            <option value="">-- Choose Product --</option>
            {productsRes?.data?.filter((p) => p.has_expiry).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.sku})
              </option>
            ))}
          </select>
        </div>

        {selectedProductId ? (
          <Table columns={columns} data={fefoBatchesRes?.data || []} keyExtractor={(b) => b.batch_id} isLoading={isFefoLoading} emptyMessage="No pickable FEFO batches found for this product." />
        ) : (
          <div style={{ padding: '3rem', textAlign: 'center', backgroundColor: 'var(--color-surface)', border: '1px dashed var(--color-border)', borderRadius: 'var(--radius-lg)', color: 'var(--color-text-muted)' }}>
            Select an expiry-tracked product from the dropdown above to inspect FEFO-ranked pickable batches.
          </div>
        )}
      </div>

      {/* FEFO Allocation Preview Modal */}
      <Modal isOpen={isPreviewModalOpen} onClose={() => setIsPreviewModalOpen(false)} title="FEFO Allocation Preview" maxWidth="lg">
        {/* PROMINENT READ-ONLY NOTICE BANNER PER ARCHITECTURAL DIRECTIVE */}
        <div style={{ padding: '0.875rem 1rem', backgroundColor: 'var(--color-warning-bg)', border: '1px solid rgba(245, 158, 11, 0.4)', borderRadius: 'var(--radius-md)', color: '#fcd34d', fontSize: '0.875rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <AlertTriangle size={24} style={{ flexShrink: 0 }} />
          <div>
            <strong style={{ display: 'block' }}>READ-ONLY ALLOCATION PREVIEW</strong>
            <span>No inventory will be reserved or deducted from the database. This is a read-only stock pick calculation.</span>
          </div>
        </div>

        <form onSubmit={handleGeneratePreview} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', marginBottom: '1.5rem' }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>Target Product</label>
            <select
              value={reqProduct}
              onChange={(e) => setReqProduct(e.target.value)}
              required
              style={{ width: '100%', padding: '0.625rem', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' }}
            >
              <option value="">-- Choose Product --</option>
              {productsRes?.data?.filter((p) => p.has_expiry).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>
          <div style={{ width: '120px' }}>
            <Input label="Quantity" type="number" value={reqQuantity} onChange={(e) => setReqQuantity(e.target.value)} required />
          </div>
          <Button type="submit" isLoading={previewMutation.isPending}>
            Calculate Plan
          </Button>
        </form>

        {allocationPlan && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ padding: '0.75rem 1rem', backgroundColor: 'var(--color-border-subtle)', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
              <span>Requested: <strong>{allocationPlan.requested_quantity}</strong> units</span>
              <span>Allocated Total: <strong style={{ color: 'var(--color-primary)' }}>{allocationPlan.allocated_total}</strong> units</span>
              <span>Status: <strong style={{ color: allocationPlan.is_fully_allocated ? 'var(--color-primary)' : 'var(--color-warning)' }}>{allocationPlan.is_fully_allocated ? 'Fully Allocated' : 'Partial Stock'}</strong></span>
            </div>

            <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-secondary)', marginTop: '0.5rem' }}>Allocated Pick Items (FEFO Ranked):</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {allocationPlan.allocations.map((alloc) => (
                <div key={alloc.batch_id} style={{ padding: '0.75rem 1rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>Rank #{alloc.fefo_rank} — Batch: {alloc.batch_number}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                      Expires: {formatDate(alloc.expiry_date)} ({alloc.days_to_expiry}d left) • Location: {alloc.location_code || 'Unassigned'}
                    </div>
                  </div>
                  <Badge variant="success">Allocate {alloc.allocated_quantity} Units</Badge>
                </div>
              ))}
            </div>
          </div>
        )}
      </Modal>

      {/* FEFO Selection Verification Modal */}
      <Modal isOpen={isVerifyModalOpen} onClose={() => setIsVerifyModalOpen(false)} title="Verify Batch Pick Selection" subtitle="Evaluate selection compliance & audit potential violations">
        <form onSubmit={handleVerifySelection} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.25rem' }}>
          <div>
            <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>Target Product *</label>
            <select
              value={verProduct}
              onChange={(e) => setVerProduct(e.target.value)}
              required
              style={{ width: '100%', padding: '0.625rem', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' }}
            >
              <option value="">-- Choose Product --</option>
              {productsRes?.data?.filter((p) => p.has_expiry).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>

          <Input label="Selected Batch ID *" placeholder="Paste batch UUID to test" value={verBatchId} onChange={(e) => setVerBatchId(e.target.value)} required />
          <Input label="Pick Quantity *" type="number" value={verQuantity} onChange={(e) => setVerQuantity(e.target.value)} required />
          <Input label="Override Reason (If bypassing earlier stock)" placeholder="e.g. Customer explicitly requested longer shelf life" value={verReason} onChange={(e) => setVerReason(e.target.value)} />

          <Button type="submit" isLoading={verifyMutation.isPending}>
            Verify Compliance
          </Button>
        </form>

        {verificationResult && (
          <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', backgroundColor: verificationResult.is_compliant ? 'var(--color-success-bg)' : 'var(--color-warning-bg)', border: `1px solid ${verificationResult.is_compliant ? 'rgba(16, 185, 129, 0.4)' : 'rgba(245, 158, 11, 0.4)'}` }}>
            {verificationResult.is_compliant ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--color-success)' }}>
                <CheckCircle size={24} />
                <div>
                  <strong>FEFO Selection Compliant</strong>
                  <p style={{ fontSize: '0.875rem' }}>Selected batch complies with FEFO stock picking rules.</p>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', color: '#fcd34d' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <AlertTriangle size={24} />
                  <strong>FEFO Selection Violation Warning</strong>
                </div>
                <p style={{ fontSize: '0.875rem' }}>{verificationResult.warning_message}</p>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: '0.5rem' }}>
                  Audit Log Created: {verificationResult.audit_logged ? 'YES (Recorded in Inventory Transactions)' : 'NO'}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};
