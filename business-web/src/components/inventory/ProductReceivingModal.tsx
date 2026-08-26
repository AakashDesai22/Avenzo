/**
 * AVENZO Business Web — Product Receiving Workflow Modal
 * Guided step-by-step receiving workflow for Inventory Managers:
 * Supplier / Factory -> Incoming Product Batch -> Receive Record -> Warehouse Location Bin -> Inventory Stock
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProductsApi } from '../../api/products.api';
import { getSuppliersApi } from '../../api/suppliers.api';
import { getWarehousesApi, createBatchApi, adjustInventoryApi } from '../../api/inventory.api';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { CheckCircle2, ArrowRight, ArrowLeft, PackageCheck } from 'lucide-react';

interface ProductReceivingModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ProductReceivingModal: React.FC<ProductReceivingModalProps> = ({ isOpen, onClose }) => {
  const queryClient = useQueryClient();
  const [step, setStep] = useState<number>(1);

  // Form states
  const [productId, setProductId] = useState('');
  const [supplierId, setSupplierId] = useState('');
  const [batchNumber, setBatchNumber] = useState('');
  const [mfgDate, setMfgDate] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [quantity, setQuantity] = useState('');
  const [warehouseId, setWarehouseId] = useState('');
  const [locationId, setLocationId] = useState('');
  const [notes, setNotes] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  // Queries
  const { data: productsRes } = useQuery({
    queryKey: ['productsAll'],
    queryFn: () => getProductsApi({ limit: 100 }),
    enabled: isOpen,
  });

  const { data: suppliersRes } = useQuery({
    queryKey: ['suppliersAll'],
    queryFn: () => getSuppliersApi(),
    enabled: isOpen,
  });

  const { data: warehousesRes } = useQuery({
    queryKey: ['warehousesAll'],
    queryFn: () => getWarehousesApi(),
    enabled: isOpen,
  });

  const selectedProduct = productsRes?.data?.find((p) => p.id === productId);
  const selectedSupplier = suppliersRes?.data?.find((s) => s.id === supplierId);
  const selectedWarehouse = warehousesRes?.data?.find((w) => w.id === warehouseId);
  const selectedLocation = selectedWarehouse?.locations?.find((l) => l.id === locationId);

  const resetForm = () => {
    setStep(1);
    setProductId('');
    setSupplierId('');
    setBatchNumber('');
    setMfgDate('');
    setExpiryDate('');
    setQuantity('');
    setWarehouseId('');
    setLocationId('');
    setNotes('');
    setFormError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const receiveMutation = useMutation({
    mutationFn: async () => {
      // 1. Create product batch record
      const batchRes = await createBatchApi({
        product_id: productId,
        batch_number: batchNumber,
        manufacturing_date: mfgDate || undefined,
        expiry_date: expiryDate || undefined,
        supplier_id: supplierId || undefined,
        initial_quantity: parseInt(quantity, 10),
        notes: notes ? `[Receiving Workflow] ${notes}` : '[Receiving Workflow] Initial Stock Receipt',
      });

      if (!batchRes.success || !batchRes.data) {
        throw new Error(batchRes.error?.message || 'Failed to create batch record.');
      }

      const newBatch = batchRes.data;

      // 2. Adjust inventory stock level to record stock receipt
      const invRes = await adjustInventoryApi({
        product_id: productId,
        batch_id: newBatch.id,
        warehouse_id: warehouseId,
        location_id: locationId || undefined,
        quantity_change: parseInt(quantity, 10),
        transaction_type: 'RECEIPT',
        notes: notes ? `Stock Received from Batch ${batchNumber}: ${notes}` : `Stock Received from Batch ${batchNumber}`,
      });

      if (!invRes.success) {
        throw new Error(invRes.error?.message || 'Failed to record inventory stock receipt.');
      }

      return invRes.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
      queryClient.invalidateQueries({ queryKey: ['expirySummary'] });
      queryClient.invalidateQueries({ queryKey: ['riskMetrics'] });
      queryClient.invalidateQueries({ queryKey: ['inventoryTransactions'] });
      handleClose();
    },
    onError: (err: any) => {
      setFormError(err.message || 'Product receiving workflow failed.');
    },
  });

  const validateNextStep = () => {
    setFormError(null);
    if (step === 1) {
      if (!productId) {
        setFormError('Please select a product.');
        return false;
      }
    } else if (step === 2) {
      if (!batchNumber) {
        setFormError('Batch Number is required.');
        return false;
      }
      if (mfgDate && expiryDate && new Date(expiryDate) < new Date(mfgDate)) {
        setFormError('Expiry date cannot precede manufacturing date.');
        return false;
      }
    } else if (step === 3) {
      if (!quantity || parseInt(quantity, 10) <= 0) {
        setFormError('Received quantity must be greater than zero.');
        return false;
      }
      if (!warehouseId) {
        setFormError('Please select a receiving warehouse.');
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateNextStep()) {
      setStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setFormError(null);
    setStep((prev) => Math.max(1, prev - 1));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateNextStep()) {
      receiveMutation.mutate();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Product Batch Receiving Workflow"
      subtitle={`Step ${step} of 4 — Record incoming inventory batch into warehouse facility`}
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {formError && (
          <div
            style={{
              padding: '0.75rem',
              backgroundColor: 'var(--color-danger-bg)',
              color: '#fca5a5',
              borderRadius: '0.375rem',
              fontSize: '0.875rem',
            }}
          >
            {formError}
          </div>
        )}

        {/* Step Indicator Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)', paddingBottom: '0.75rem' }}>
          {['1. Product & Supplier', '2. Batch & Dates', '3. Quantity & Bin', '4. Review & Receive'].map((label, idx) => {
            const stepNum = idx + 1;
            const isCurrent = step === stepNum;
            const isDone = step > stepNum;
            return (
              <span
                key={stepNum}
                style={{
                  fontSize: '0.75rem',
                  fontWeight: isCurrent || isDone ? 700 : 500,
                  color: isCurrent ? 'var(--color-primary)' : isDone ? '#166534' : 'var(--color-text-muted)',
                }}
              >
                {label}
              </span>
            );
          })}
        </div>

        {/* Step 1: Product & Supplier Selection */}
        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>
                Incoming Product *
              </label>
              <select
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '0.625rem',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '0.375rem',
                  color: 'var(--color-text-primary)',
                }}
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
              <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>
                Supplier / Manufacturer (Optional)
              </label>
              <select
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.625rem',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '0.375rem',
                  color: 'var(--color-text-primary)',
                }}
              >
                <option value="">-- Select Supplier --</option>
                {suppliersRes?.data?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} ({s.contact_person || 'General Supplier'})
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Step 2: Batch Number & Dates */}
        {step === 2 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Input
              label="Batch / Lot Number *"
              placeholder="e.g. LOT-2026-AUG-880"
              value={batchNumber}
              onChange={(e) => setBatchNumber(e.target.value)}
              required
            />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <Input label="Manufacturing Date" type="date" value={mfgDate} onChange={(e) => setMfgDate(e.target.value)} />
              <Input label="Expiry Date *" type="date" value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} required />
            </div>
          </div>
        )}

        {/* Step 3: Quantity & Warehouse Bin */}
        {step === 3 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <Input
              label="Received Initial Quantity (Units) *"
              type="number"
              placeholder="e.g. 500"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              required
            />

            <div>
              <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>
                Target Receiving Warehouse *
              </label>
              <select
                value={warehouseId}
                onChange={(e) => {
                  setWarehouseId(e.target.value);
                  setLocationId('');
                }}
                required
                style={{
                  width: '100%',
                  padding: '0.625rem',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '0.375rem',
                  color: 'var(--color-text-primary)',
                }}
              >
                <option value="">-- Select Warehouse --</option>
                {warehousesRes?.data?.map((w) => (
                  <option key={w.id} value={w.id}>
                    {w.name} ({w.city || 'Primary'})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>
                Warehouse Location Bin (Optional)
              </label>
              <select
                value={locationId}
                onChange={(e) => setLocationId(e.target.value)}
                disabled={!warehouseId}
                style={{
                  width: '100%',
                  padding: '0.625rem',
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '0.375rem',
                  color: 'var(--color-text-primary)',
                }}
              >
                <option value="">-- Unassigned / Default Bin --</option>
                {selectedWarehouse?.locations?.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.location_code} ({loc.description || 'Bin Location'})
                  </option>
                ))}
              </select>
            </div>

            <Input label="Receiving Notes" placeholder="Carrier / Delivery invoice notes..." value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
        )}

        {/* Step 4: Summary Review */}
        {step === 4 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem', backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '0.375rem', border: '1px solid #e2e8f0' }}>
            <h4 style={{ fontSize: '0.9375rem', fontWeight: 700, color: '#0f172a', margin: 0, display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
              <PackageCheck size={18} color="#2563eb" /> Verify Incoming Shipment Details
            </h4>
            <div style={{ fontSize: '0.8125rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div><strong>Product:</strong> {selectedProduct?.name} ({selectedProduct?.sku})</div>
              <div><strong>Supplier:</strong> {selectedSupplier?.name || 'General Supplier'}</div>
              <div><strong>Batch Number:</strong> {batchNumber}</div>
              <div><strong>Expiry Date:</strong> {expiryDate || 'N/A'}</div>
              <div><strong>Received Quantity:</strong> {quantity} units</div>
              <div><strong>Warehouse:</strong> {selectedWarehouse?.name}</div>
              <div><strong>Bin Location:</strong> {selectedLocation?.location_code || 'Default Storage'}</div>
              <div><strong>Notes:</strong> {notes || 'None'}</div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem' }}>
          {step > 1 ? (
            <Button type="button" variant="secondary" onClick={handleBack}>
              <ArrowLeft size={16} /> Back
            </Button>
          ) : (
            <Button type="button" variant="secondary" onClick={handleClose}>
              Cancel
            </Button>
          )}

          {step < 4 ? (
            <Button type="button" onClick={handleNext}>
              Next Step <ArrowRight size={16} />
            </Button>
          ) : (
            <Button type="submit" isLoading={receiveMutation.isPending}>
              <CheckCircle2 size={16} /> Record & Receive Batch
            </Button>
          )}
        </div>
      </form>
    </Modal>
  );
};
