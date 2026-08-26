/**
 * AVENZO Business Web — Batch Management & Receiving Page
 * Track product manufacturing, supplier records, expiry dates, DTE classifications,
 * and record incoming shipments via guided receiving workflow.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBatchesApi, createBatchApi } from '../api/inventory.api';
import { getProductsApi } from '../api/products.api';
import { getSuppliersApi } from '../api/suppliers.api';
import { Batch, BatchCreate } from '../types/inventory';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { formatDate } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { ProductReceivingModal } from '../components/inventory/ProductReceivingModal';
import { BatchRecallModal } from '../components/inventory/BatchRecallModal';
import { Plus, PackageCheck, ShieldAlert } from 'lucide-react';

export const BatchesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { can, hasRole } = useAuth();
  const canCreate = can('create_batches');
  const canRecall = hasRole(['ADMIN', 'BUSINESS_MANAGER']);

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isReceivingModalOpen, setIsReceivingModalOpen] = useState(false);
  const [isRecallModalOpen, setIsRecallModalOpen] = useState(false);
  const [selectedRecallBatch, setSelectedRecallBatch] = useState<Batch | null>(null);

  // Form states for manual batch creation
  const [productId, setProductId] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const [batchNumber, setBatchNumber] = useState('');
  const [mfgDate, setMfgDate] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [initialQty, setInitialQty] = useState('');
  const [notes, setNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data: batchesRes, isLoading } = useQuery({
    queryKey: ['batches'],
    queryFn: () => getBatchesApi(),
  });

  const { data: productsRes } = useQuery({
    queryKey: ['productsAll'],
    queryFn: () => getProductsApi({ limit: 100 }),
    enabled: isCreateModalOpen,
  });

  const { data: suppliersRes } = useQuery({
    queryKey: ['suppliersAll'],
    queryFn: () => getSuppliersApi(),
    enabled: isCreateModalOpen,
  });

  const createMutation = useMutation({
    mutationFn: (data: BatchCreate) => createBatchApi(data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['batches'] });
        queryClient.invalidateQueries({ queryKey: ['inventory'] });
        closeCreateModal();
      } else {
        setFormError(res.error?.message || 'Failed to create batch.');
      }
    },
  });

  const closeCreateModal = () => {
    setIsCreateModalOpen(false);
    setProductId('');
    setSupplierId('');
    setBatchNumber('');
    setMfgDate('');
    setExpiryDate('');
    setInitialQty('');
    setNotes('');
    setFormError(null);
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!productId || !batchNumber) {
      setFormError('Product and Batch Number are required.');
      return;
    }

    if (mfgDate && expiryDate && new Date(expiryDate) < new Date(mfgDate)) {
      setFormError('Expiry date cannot precede manufacturing date.');
      return;
    }

    createMutation.mutate({
      product_id: productId,
      supplier_id: supplierId || undefined,
      batch_number: batchNumber,
      manufacturing_date: mfgDate || undefined,
      expiry_date: expiryDate || undefined,
      initial_quantity: initialQty ? parseInt(initialQty, 10) : 0,
      notes: notes || undefined,
    });
  };

  const getDteStatus = (batch: Batch) => {
    if (batch.status === 'recalled') {
      return { label: 'RECALLED', variant: 'danger' as const, dte: 'SAFETY RECALL' };
    }
    const expDate = batch.expiry_date;
    if (!expDate) return { label: 'SAFE', variant: 'success' as const, dte: 'N/A' };
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const exp = new Date(expDate);
    exp.setHours(0, 0, 0, 0);

    const diffDays = Math.ceil((exp.getTime() - today.getTime()) / (1000 * 3600 * 24));
    if (diffDays < 0) return { label: 'EXPIRED', variant: 'danger' as const, dte: `${Math.abs(diffDays)}d expired` };
    if (diffDays <= 7) return { label: 'CRITICAL', variant: 'danger' as const, dte: `${diffDays}d left` };
    if (diffDays <= 30) return { label: 'EXPIRING_SOON', variant: 'warning' as const, dte: `${diffDays}d left` };
    return { label: 'SAFE', variant: 'success' as const, dte: `${diffDays}d left` };
  };

  const handleOpenRecallModal = (batch: Batch) => {
    setSelectedRecallBatch(batch);
    setIsRecallModalOpen(true);
  };

  const columns: Column<Batch>[] = [
    { key: 'batch_number', header: 'Batch Number', render: (b) => <span style={{ fontWeight: 600 }}>{b.batch_number}</span> },
    { key: 'product', header: 'Product Name', render: (b) => b.product?.name || 'N/A' },
    { key: 'sku', header: 'SKU', render: (b) => b.product?.sku || 'N/A' },
    { key: 'supplier', header: 'Supplier', render: (b) => b.supplier?.name || 'General Supplier' },
    { key: 'mfg_date', header: 'Mfg Date', render: (b) => formatDate(b.manufacturing_date) },
    { key: 'expiry_date', header: 'Expiry Date', render: (b) => formatDate(b.expiry_date) },
    {
      key: 'dte',
      header: 'Expiry Status (DTE)',
      render: (b) => {
        const dteInfo = getDteStatus(b);
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
            <Badge status={dteInfo.label} />
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>({dteInfo.dte})</span>
          </div>
        );
      },
    },
    { key: 'initial_quantity', header: 'Initial Qty', render: (b) => b.initial_quantity.toLocaleString() },
    {
      key: 'actions',
      header: 'Actions',
      render: (b) => {
        if (b.status === 'recalled') {
          return (
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#991b1b', backgroundColor: '#fef2f2', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
              RECALLED
            </span>
          );
        }
        if (!canRecall) return null;
        return (
          <Button
            size="sm"
            variant="danger"
            onClick={() => handleOpenRecallModal(b)}
            style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', backgroundColor: '#991b1b' }}
          >
            <ShieldAlert size={14} style={{ marginRight: '0.25rem' }} /> Recall
          </Button>
        );
      },
    },
  ];

  return (
    <div>
      <Header
        title="Batch Management & Product Receiving"
        subtitle="Track product manufacturing, supplier records, and incoming shipments"
        action={
          canCreate ? (
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <Button variant="secondary" onClick={() => setIsCreateModalOpen(true)}>
                <Plus size={18} /> Quick Batch Record
              </Button>
              <Button onClick={() => setIsReceivingModalOpen(true)}>
                <PackageCheck size={18} /> Receive Product Batch
              </Button>
            </div>
          ) : null
        }
      />

      <div style={{ padding: '2rem' }}>
        <Table columns={columns} data={batchesRes?.data || []} keyExtractor={(b) => b.id} isLoading={isLoading} />
      </div>

      {/* Manual Batch Record Modal */}
      <Modal isOpen={isCreateModalOpen} onClose={closeCreateModal} title="Create Product Batch Record" subtitle="Record new batch metadata and supplier dates">
        <form onSubmit={handleCreateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {formError && (
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--color-danger-bg)', color: '#fca5a5', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
              {formError}
            </div>
          )}

          <div>
            <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>Product *</label>
            <select
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
              required
              style={{ width: '100%', padding: '0.625rem', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' }}
            >
              <option value="">-- Select Product --</option>
              {productsRes?.data?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>Supplier (Optional)</label>
            <select
              value={supplierId}
              onChange={(e) => setSupplierId(e.target.value)}
              style={{ width: '100%', padding: '0.625rem', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' }}
            >
              <option value="">-- Select Supplier --</option>
              {suppliersRes?.data?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <Input label="Batch Number *" placeholder="e.g. BATCH-2026-001" value={batchNumber} onChange={(e) => setBatchNumber(e.target.value)} required />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input label="Manufacturing Date" type="date" value={mfgDate} onChange={(e) => setMfgDate(e.target.value)} />
            <Input label="Expiry Date" type="date" value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} />
          </div>

          <Input label="Initial Quantity" type="number" value={initialQty} onChange={(e) => setInitialQty(e.target.value)} />
          <Input label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={closeCreateModal}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Batch Record
            </Button>
          </div>
        </form>
      </Modal>

      {/* Guided Receiving Workflow Modal */}
      <ProductReceivingModal isOpen={isReceivingModalOpen} onClose={() => setIsReceivingModalOpen(false)} />

      {/* Batch Safety Recall Modal */}
      <BatchRecallModal
        isOpen={isRecallModalOpen}
        onClose={() => setIsRecallModalOpen(false)}
        batch={selectedRecallBatch}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['batches'] });
          queryClient.invalidateQueries({ queryKey: ['inventory'] });
        }}
      />
    </div>
  );
};
