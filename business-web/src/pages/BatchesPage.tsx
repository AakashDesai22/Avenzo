import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBatchesApi, createBatchApi } from '../api/inventory.api';
import { getProductsApi } from '../api/products.api';
import { Batch, BatchCreate } from '../types/inventory';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { formatDate } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { Plus } from 'lucide-react';

export const BatchesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { can } = useAuth();
  const canCreate = can('create_batches');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form states
  const [productId, setProductId] = useState('');
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
    enabled: isModalOpen,
  });

  const createMutation = useMutation({
    mutationFn: (data: BatchCreate) => createBatchApi(data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['batches'] });
        queryClient.invalidateQueries({ queryKey: ['inventory'] });
        closeModal();
      } else {
        setFormError(res.error?.message || 'Failed to create batch.');
      }
    },
  });

  const closeModal = () => {
    setIsModalOpen(false);
    setProductId('');
    setBatchNumber('');
    setMfgDate('');
    setExpiryDate('');
    setInitialQty('');
    setNotes('');
    setFormError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
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
      batch_number: batchNumber,
      manufacturing_date: mfgDate || undefined,
      expiry_date: expiryDate || undefined,
      initial_quantity: initialQty ? parseInt(initialQty, 10) : 0,
      notes: notes || undefined,
    });
  };

  const columns: Column<Batch>[] = [
    { key: 'batch_number', header: 'Batch Number', render: (b) => <span style={{ fontWeight: 600 }}>{b.batch_number}</span> },
    { key: 'product', header: 'Product Name', render: (b) => b.product?.name || 'N/A' },
    { key: 'sku', header: 'SKU', render: (b) => b.product?.sku || 'N/A' },
    { key: 'mfg_date', header: 'Mfg Date', render: (b) => formatDate(b.manufacturing_date) },
    { key: 'expiry_date', header: 'Expiry Date', render: (b) => formatDate(b.expiry_date) },
    {
      key: 'status',
      header: 'Batch Status',
      render: (b) => (
        <Badge variant={b.status === 'active' ? 'success' : 'danger'}>{b.status.toUpperCase()}</Badge>
      ),
    },
    { key: 'initial_quantity', header: 'Initial Qty', render: (b) => b.initial_quantity.toLocaleString() },
  ];

  return (
    <div>
      <Header
        title="Batch Management"
        subtitle="Track product manufacturing and expiry dates"
        action={
          canCreate ? (
            <Button onClick={() => setIsModalOpen(true)}>
              <Plus size={18} /> Create New Batch
            </Button>
          ) : null
        }
      />

      <div style={{ padding: '2rem' }}>
        <Table columns={columns} data={batchesRes?.data || []} keyExtractor={(b) => b.id} isLoading={isLoading} />
      </div>

      <Modal isOpen={isModalOpen} onClose={closeModal} title="Create Product Batch" subtitle="Record new batch metadata and expiry dates">
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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

          <Input label="Batch Number *" placeholder="e.g. BATCH-2026-001" value={batchNumber} onChange={(e) => setBatchNumber(e.target.value)} required />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input label="Manufacturing Date" type="date" value={mfgDate} onChange={(e) => setMfgDate(e.target.value)} />
            <Input label="Expiry Date" type="date" value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} />
          </div>

          <Input label="Initial Quantity" type="number" value={initialQty} onChange={(e) => setInitialQty(e.target.value)} />
          <Input label="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={closeModal}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Batch
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
