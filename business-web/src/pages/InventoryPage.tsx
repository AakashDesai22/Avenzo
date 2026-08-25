import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getInventoryApi,
  getWarehousesApi,
  getBatchesApi,
  getInventoryTransactionsApi,
  adjustInventoryApi,
} from '../api/inventory.api';
import { getProductsApi } from '../api/products.api';
import { Inventory, InventoryTransaction } from '../types/inventory';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { formatDate } from '../utils/formatters';
import { SlidersHorizontal, History } from 'lucide-react';

export const InventoryPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'balances' | 'audit'>('balances');

  const [selectedWarehouse, setSelectedWarehouse] = useState<string>('');
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false);

  // Form state for Stock Adjustment
  const [adjProductId, setAdjProductId] = useState('');
  const [adjBatchId, setAdjBatchId] = useState('');
  const [adjWarehouseId, setAdjWarehouseId] = useState('');
  const [adjQuantityChange, setAdjQuantityChange] = useState('');
  const [adjType, setAdjType] = useState('RECEIPT');
  const [adjNotes, setAdjNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data: inventoryRes, isLoading: isInvLoading } = useQuery({
    queryKey: ['inventory', selectedWarehouse],
    queryFn: () => getInventoryApi({ warehouse_id: selectedWarehouse || undefined }),
  });

  const { data: txRes, isLoading: isTxLoading } = useQuery({
    queryKey: ['inventoryTransactions'],
    queryFn: () => getInventoryTransactionsApi(),
    enabled: activeTab === 'audit',
  });

  const { data: warehousesRes } = useQuery({
    queryKey: ['warehouses'],
    queryFn: () => getWarehousesApi(),
  });

  const { data: productsRes } = useQuery({
    queryKey: ['productsAll'],
    queryFn: () => getProductsApi({ limit: 100 }),
    enabled: isAdjustModalOpen,
  });

  const { data: batchesRes } = useQuery({
    queryKey: ['batchesForProduct', adjProductId],
    queryFn: () => getBatchesApi({ product_id: adjProductId || undefined }),
    enabled: isAdjustModalOpen && !!adjProductId,
  });

  const adjustMutation = useMutation({
    mutationFn: (data: any) => adjustInventoryApi(data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['inventory'] });
        queryClient.invalidateQueries({ queryKey: ['expirySummary'] });
        queryClient.invalidateQueries({ queryKey: ['riskMetrics'] });
        queryClient.invalidateQueries({ queryKey: ['inventoryTransactions'] });
        closeAdjustModal();
      } else {
        setFormError(res.error?.message || 'Stock adjustment failed.');
      }
    },
  });

  const closeAdjustModal = () => {
    setIsAdjustModalOpen(false);
    setAdjProductId('');
    setAdjBatchId('');
    setAdjWarehouseId('');
    setAdjQuantityChange('');
    setAdjType('RECEIPT');
    setAdjNotes('');
    setFormError(null);
  };

  const handleOpenAdjust = () => {
    if (warehousesRes?.data && warehousesRes.data.length > 0) {
      setAdjWarehouseId(warehousesRes.data[0].id);
    }
    setIsAdjustModalOpen(true);
  };

  const handleSubmitAdjust = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!adjProductId || !adjBatchId || !adjWarehouseId || !adjQuantityChange) {
      setFormError('Please fill in all required fields.');
      return;
    }

    const qtyNum = parseInt(adjQuantityChange, 10);
    if (isNaN(qtyNum) || qtyNum === 0) {
      setFormError('Quantity change must be a non-zero integer.');
      return;
    }

    adjustMutation.mutate({
      product_id: adjProductId,
      batch_id: adjBatchId,
      warehouse_id: adjWarehouseId,
      quantity_change: qtyNum,
      transaction_type: adjType,
      notes: adjNotes || undefined,
    });
  };

  const invColumns: Column<Inventory>[] = [
    { key: 'product', header: 'Product', render: (i) => <span style={{ fontWeight: 600 }}>{i.product?.name}</span> },
    { key: 'sku', header: 'SKU', render: (i) => i.product?.sku },
    { key: 'batch', header: 'Batch', render: (i) => i.batch?.batch_number },
    { key: 'expiry', header: 'Expiry Date', render: (i) => formatDate(i.batch?.expiry_date) },
    { key: 'warehouse', header: 'Warehouse', render: (i) => i.warehouse?.name },
    { key: 'location', header: 'Location', render: (i) => i.location?.location_code || 'Unassigned' },
    { key: 'quantity_on_hand', header: 'On Hand', render: (i) => i.quantity_on_hand.toLocaleString() },
    { key: 'quantity_reserved', header: 'Reserved', render: (i) => i.quantity_reserved.toLocaleString() },
    {
      key: 'quantity_available',
      header: 'Available Stock',
      render: (i) => <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{i.quantity_available.toLocaleString()}</span>,
    },
  ];

  const txColumns: Column<InventoryTransaction>[] = [
    { key: 'type', header: 'Type', render: (t) => <Badge variant={t.transaction_type === 'FEFO_VIOLATION' ? 'warning' : 'info'}>{t.transaction_type}</Badge> },
    {
      key: 'change',
      header: 'Qty Change',
      render: (t) => (
        <span style={{ fontWeight: 600, color: t.quantity_change > 0 ? 'var(--color-primary)' : t.quantity_change < 0 ? 'var(--color-danger)' : 'var(--color-text-secondary)' }}>
          {t.quantity_change > 0 ? `+${t.quantity_change}` : t.quantity_change}
        </span>
      ),
    },
    { key: 'before', header: 'Before', render: (t) => t.quantity_before },
    { key: 'after', header: 'After', render: (t) => t.quantity_after },
    { key: 'notes', header: 'Audit Notes', render: (t) => t.notes || 'N/A' },
    { key: 'created_at', header: 'Timestamp', render: (t) => formatDate(t.created_at) },
  ];

  return (
    <div>
      <Header
        title="Inventory Management"
        subtitle="Live stock balances, location bins, and stock adjustments"
        action={
          <Button onClick={handleOpenAdjust}>
            <SlidersHorizontal size={18} /> Adjust Stock Level
          </Button>
        }
      />

      <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--color-border)' }}>
          <button
            onClick={() => setActiveTab('balances')}
            style={{
              padding: '0.625rem 1.25rem',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'balances' ? '2px solid var(--color-primary)' : '2px solid transparent',
              color: activeTab === 'balances' ? 'var(--color-primary)' : 'var(--color-text-secondary)',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Stock Balances
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            style={{
              padding: '0.625rem 1.25rem',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === 'audit' ? '2px solid var(--color-primary)' : '2px solid transparent',
              color: activeTab === 'audit' ? 'var(--color-primary)' : 'var(--color-text-secondary)',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <History size={16} /> Audit Movement Log
          </button>
        </div>

        {activeTab === 'balances' ? (
          <>
            {/* Warehouse Filter */}
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <select
                value={selectedWarehouse}
                onChange={(e) => setSelectedWarehouse(e.target.value)}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--color-text-primary)',
                }}
              >
                <option value="">All Warehouses</option>
                {warehousesRes?.data?.map((wh) => (
                  <option key={wh.id} value={wh.id}>
                    {wh.name}
                  </option>
                ))}
              </select>
            </div>

            <Table columns={invColumns} data={inventoryRes?.data || []} keyExtractor={(i) => i.id} isLoading={isInvLoading} />
          </>
        ) : (
          <Table columns={txColumns} data={txRes?.data || []} keyExtractor={(t) => t.id} isLoading={isTxLoading} />
        )}
      </div>

      {/* Stock Adjustment Modal */}
      <Modal isOpen={isAdjustModalOpen} onClose={closeAdjustModal} title="Adjust Stock Level" subtitle="Record stock receipt, adjustment, or damage">
        <form onSubmit={handleSubmitAdjust} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {formError && (
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--color-danger-bg)', color: '#fca5a5', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
              {formError}
            </div>
          )}

          <div>
            <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>Product *</label>
            <select
              value={adjProductId}
              onChange={(e) => {
                setAdjProductId(e.target.value);
                setAdjBatchId('');
              }}
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
            <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>Batch *</label>
            <select
              value={adjBatchId}
              onChange={(e) => setAdjBatchId(e.target.value)}
              disabled={!adjProductId}
              required
              style={{ width: '100%', padding: '0.625rem', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' }}
            >
              <option value="">-- Select Batch --</option>
              {batchesRes?.data?.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.batch_number} (Exp: {formatDate(b.expiry_date)})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>Warehouse *</label>
            <select
              value={adjWarehouseId}
              onChange={(e) => setAdjWarehouseId(e.target.value)}
              required
              style={{ width: '100%', padding: '0.625rem', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' }}
            >
              {warehousesRes?.data?.map((wh) => (
                <option key={wh.id} value={wh.id}>
                  {wh.name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input label="Quantity Change (+ or -) *" type="number" placeholder="e.g. 50 or -10" value={adjQuantityChange} onChange={(e) => setAdjQuantityChange(e.target.value)} required />
            <div>
              <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>Transaction Type</label>
              <select
                value={adjType}
                onChange={(e) => setAdjType(e.target.value)}
                style={{ width: '100%', padding: '0.625rem', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', color: 'var(--color-text-primary)' }}
              >
                <option value="RECEIPT">RECEIPT (+)</option>
                <option value="ADJUSTMENT">ADJUSTMENT (+/-)</option>
                <option value="DAMAGE">DAMAGE (-)</option>
                <option value="EXPIRY">EXPIRY (-)</option>
              </select>
            </div>
          </div>

          <Input label="Audit Notes" placeholder="Reason for adjustment..." value={adjNotes} onChange={(e) => setAdjNotes(e.target.value)} />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={closeAdjustModal}>
              Cancel
            </Button>
            <Button type="submit" isLoading={adjustMutation.isPending}>
              Apply Adjustment
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
