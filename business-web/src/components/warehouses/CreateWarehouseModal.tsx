/**
 * AVENZO Business Web — Create Warehouse Modal Component
 * Reusable modal for inline warehouse facility creation in inventory and receiving workflows.
 */

import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createWarehouseApi } from '../../api/inventory.api';
import { Warehouse } from '../../types/inventory';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

interface CreateWarehouseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (warehouse: Warehouse) => void;
}

export const CreateWarehouseModal: React.FC<CreateWarehouseModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [city, setCity] = useState('');
  const [address, setAddress] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const resetForm = () => {
    setName('');
    setCity('');
    setAddress('');
    setFormError(null);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const createMutation = useMutation({
    mutationFn: (data: { name: string; city?: string; address?: string }) =>
      createWarehouseApi({
        name: data.name,
        city: data.city || undefined,
        address: data.address || undefined,
        is_active: true,
      }),
    onSuccess: (res) => {
      if (res.success && res.data) {
        queryClient.invalidateQueries({ queryKey: ['warehouses'] });
        queryClient.invalidateQueries({ queryKey: ['warehousesOverview'] });
        queryClient.invalidateQueries({ queryKey: ['warehousesAll'] });
        onSuccess(res.data);
        handleClose();
      } else {
        setFormError(res.error?.message || 'Failed to create warehouse facility.');
      }
    },
    onError: (err: any) => {
      setFormError(err.message || 'An unexpected error occurred while creating warehouse.');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!name.trim()) {
      setFormError('Warehouse facility name is required.');
      return;
    }

    createMutation.mutate({
      name: name.trim(),
      city: city.trim() || undefined,
      address: address.trim() || undefined,
    });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create Warehouse Facility"
      subtitle="Register a new storage location for inventory management"
    >
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {formError && (
          <div
            style={{
              padding: '0.75rem',
              backgroundColor: 'var(--color-danger-bg, rgba(239, 68, 68, 0.1))',
              color: '#f87171',
              borderRadius: 'var(--radius-md)',
              fontSize: '0.875rem',
            }}
          >
            {formError}
          </div>
        )}

        <Input
          label="Warehouse Facility Name *"
          placeholder="e.g. Central Logistics Hub"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        <Input
          label="City / Region"
          placeholder="e.g. Mumbai, Navi Mumbai, Pune"
          value={city}
          onChange={(e) => setCity(e.target.value)}
        />

        <div>
          <label
            style={{
              fontSize: '0.875rem',
              color: 'var(--color-text-secondary)',
              fontWeight: 500,
              display: 'block',
              marginBottom: '0.375rem',
            }}
          >
            Physical Address (Optional)
          </label>
          <textarea
            placeholder="e.g. Plot 42, Logistics Park, Phase II"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            rows={3}
            style={{
              width: '100%',
              padding: '0.625rem 0.75rem',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-border)',
              backgroundColor: 'var(--color-surface)',
              color: 'var(--color-text-primary)',
              fontSize: '0.875rem',
              fontFamily: 'inherit',
              resize: 'vertical',
            }}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
          <Button type="button" variant="secondary" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={createMutation.isPending}>
            Create Warehouse
          </Button>
        </div>
      </form>
    </Modal>
  );
};
