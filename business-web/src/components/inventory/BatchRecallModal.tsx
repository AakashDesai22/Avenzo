/**
 * AVENZO Business Web — Batch Recall Modal
 * Previews recall impact and allows authorized users (ADMIN / BUSINESS_MANAGER)
 * to execute product batch recalls with explicit confirmation text.
 */

import React, { useState, useEffect } from 'react';
import { Batch } from '../../types/inventory';
import { getBatchRecallImpactApi, recallBatchApi, BatchRecallImpact } from '../../api/inventory.api';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { AlertTriangle, ShieldAlert } from 'lucide-react';

interface BatchRecallModalProps {
  isOpen: boolean;
  onClose: () => void;
  batch: Batch | null;
  onSuccess: () => void;
}

export const BatchRecallModal: React.FC<BatchRecallModalProps> = ({
  isOpen,
  onClose,
  batch,
  onSuccess,
}) => {
  const [impact, setImpact] = useState<BatchRecallImpact | null>(null);
  const [isLoadingImpact, setIsLoadingImpact] = useState(false);
  const [recallReason, setRecallReason] = useState('');
  const [confirmText, setConfirmText] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && batch) {
      setIsLoadingImpact(true);
      setError(null);
      getBatchRecallImpactApi(batch.id)
        .then((res) => {
          if (res.success && res.data) {
            setImpact(res.data);
          } else {
            setError(res.error?.message || 'Failed to load recall impact preview.');
          }
        })
        .catch(() => setError('Error loading recall impact details.'))
        .finally(() => setIsLoadingImpact(false));
    } else {
      setImpact(null);
      setRecallReason('');
      setConfirmText('');
      setError(null);
    }
  }, [isOpen, batch]);

  if (!batch) return null;

  const isConfirmValid = confirmText.trim().toUpperCase() === 'CONFIRM RECALL' && recallReason.trim().length >= 3;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isConfirmValid) return;

    setIsExecuting(true);
    setError(null);

    try {
      const res = await recallBatchApi(batch.id, { recall_reason: recallReason, severity: 'HIGH' });
      if (res.success) {
        onSuccess();
        onClose();
      } else {
        setError(res.error?.message || 'Failed to execute batch recall.');
      }
    } catch {
      setError('An unexpected error occurred while executing the batch recall.');
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Initiate Safety Recall — Batch ${batch.batch_number}`}
      subtitle={`Product: ${batch.product?.name || 'N/A'}`}
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {error && (
          <div
            style={{
              padding: '0.75rem',
              backgroundColor: 'var(--color-danger-bg, #fef2f2)',
              color: '#991b1b',
              border: '1px solid #fca5a5',
              borderRadius: 'var(--radius-md, 8px)',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <AlertTriangle size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* Impact Cards Preview */}
        <div style={{ backgroundColor: 'var(--color-surface-subtle, #f8fafc)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--color-border, #e2e8f0)' }}>
          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-secondary, #475569)', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
            <ShieldAlert size={16} color="#991b1b" /> RECALL IMPACT PREVIEW
          </div>
          {isLoadingImpact ? (
            <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted, #94a3b8)' }}>Calculating impact metrics...</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem', textAlign: 'center' }}>
              <div style={{ padding: '0.75rem', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>{impact?.affected_orders_count ?? 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Delivered Orders</div>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>{impact?.affected_consumers_count ?? 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Affected Consumers</div>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #cbd5e1' }}>
                <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a' }}>{impact?.affected_pantry_items_count ?? 0}</div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Pantry Items</div>
              </div>
            </div>
          )}
        </div>

        <div>
          <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary, #475569)', display: 'block', marginBottom: '0.375rem', fontWeight: 500 }}>
            Recall Reason *
          </label>
          <Input
            placeholder="e.g. Contamination detected during quality audit"
            value={recallReason}
            onChange={(e) => setRecallReason(e.target.value)}
            required
          />
        </div>

        <div>
          <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary, #475569)', display: 'block', marginBottom: '0.375rem', fontWeight: 500 }}>
            Type "CONFIRM RECALL" to proceed *
          </label>
          <Input
            placeholder="CONFIRM RECALL"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            required
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
          <Button type="button" variant="secondary" onClick={onClose} disabled={isExecuting}>
            Cancel
          </Button>
          <Button
            type="submit"
            isLoading={isExecuting}
            disabled={!isConfirmValid || isExecuting}
            style={{ backgroundColor: '#991b1b', color: '#ffffff' }}
          >
            Execute Safety Recall
          </Button>
        </div>
      </form>
    </Modal>
  );
};
