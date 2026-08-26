/**
 * AVENZO Business Web — Warehouse Facilities Overview Page
 * Allows Inventory Managers and Admins to inspect multi-warehouse facilities, bin locations, and create storage bins.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getWarehousesApi, createWarehouseLocationApi } from '../api/inventory.api';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { useAuth } from '../context/AuthContext';
import { Building2, MapPin, Plus, Box, Layers } from 'lucide-react';

export const WarehousesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { can } = useAuth();
  const canManage = can('adjust_inventory');

  const [selectedWarehouseId, setSelectedWarehouseId] = useState<string | null>(null);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [locationCode, setLocationCode] = useState('');
  const [locationDesc, setLocationDesc] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data: warehousesRes, isLoading } = useQuery({
    queryKey: ['warehousesOverview'],
    queryFn: () => getWarehousesApi(),
  });

  const addLocationMutation = useMutation({
    mutationFn: (data: { warehouseId: string; code: string; desc?: string }) =>
      createWarehouseLocationApi(data.warehouseId, {
        location_code: data.code,
        description: data.desc,
      }),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['warehousesOverview'] });
        queryClient.invalidateQueries({ queryKey: ['warehouses'] });
        closeLocationModal();
      } else {
        setFormError(res.error?.message || 'Failed to add location bin.');
      }
    },
  });

  const closeLocationModal = () => {
    setIsLocationModalOpen(false);
    setSelectedWarehouseId(null);
    setLocationCode('');
    setLocationDesc('');
    setFormError(null);
  };

  const handleOpenAddLocation = (whId: string) => {
    setSelectedWarehouseId(whId);
    setIsLocationModalOpen(true);
  };

  const handleAddLocationSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!locationCode || !selectedWarehouseId) {
      setFormError('Location code is required.');
      return;
    }

    addLocationMutation.mutate({
      warehouseId: selectedWarehouseId,
      code: locationCode,
      desc: locationDesc || undefined,
    });
  };

  const warehouses = warehousesRes?.data || [];

  return (
    <div>
      <Header
        title="Warehouse Facilities"
        subtitle="Multi-facility oversight, storage bins, and physical location management"
      />

      <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            Loading warehouse facilities...
          </div>
        ) : warehouses.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
            No warehouse facilities configured.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.25rem' }}>
            {warehouses.map((wh) => (
              <div
                key={wh.id}
                style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '0.5rem',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '1rem',
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                      <div
                        style={{
                          padding: '0.5rem',
                          borderRadius: '0.375rem',
                          backgroundColor: '#eff6ff',
                          color: '#2563eb',
                        }}
                      >
                        <Building2 size={24} />
                      </div>
                      <div>
                        <h3 style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--color-text-primary)', margin: 0 }}>
                          {wh.name}
                        </h3>
                        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', margin: '0.125rem 0 0', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <MapPin size={12} /> {wh.city ? `${wh.address || 'Facility'}, ${wh.city}` : wh.address || 'Primary Facility'}
                        </p>
                      </div>
                    </div>
                    <Badge variant={wh.is_active ? 'success' : 'neutral'}>
                      {wh.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </Badge>
                  </div>

                  {/* Storage Bin Locations */}
                  <div style={{ marginTop: '1rem', borderTop: '1px solid var(--color-border)', paddingTop: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                        <Box size={14} /> Storage Bins ({wh.locations?.length || 0})
                      </span>
                      {canManage && (
                        <button
                          onClick={() => handleOpenAddLocation(wh.id)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#2563eb',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                          }}
                        >
                          <Plus size={12} /> Add Bin
                        </button>
                      )}
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                      {wh.locations && wh.locations.length > 0 ? (
                        wh.locations.map((loc) => (
                          <span
                            key={loc.id}
                            style={{
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              padding: '0.25rem 0.5rem',
                              backgroundColor: 'var(--color-border-subtle)',
                              borderRadius: '0.25rem',
                              color: 'var(--color-text-primary)',
                              border: '1px solid var(--color-border)',
                            }}
                            title={loc.description}
                          >
                            {loc.location_code}
                          </span>
                        ))
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                          No bin locations defined
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--color-border)', paddingTop: '0.75rem', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                  <span>Facility ID: {wh.id.substring(0, 8)}...</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><Layers size={12} /> Live Stock Sync Active</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Bin Location Modal */}
      <Modal isOpen={isLocationModalOpen} onClose={closeLocationModal} title="Add Warehouse Bin Location" subtitle="Create a storage bin or aisle location">
        <form onSubmit={handleAddLocationSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {formError && (
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--color-danger-bg)', color: '#fca5a5', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
              {formError}
            </div>
          )}

          <Input label="Bin Location Code *" placeholder="e.g. BIN-A1-SECTION2" value={locationCode} onChange={(e) => setLocationCode(e.target.value)} required />
          <Input label="Description (Optional)" placeholder="e.g. Cold storage shelf A1" value={locationDesc} onChange={(e) => setLocationDesc(e.target.value)} />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={closeLocationModal}>
              Cancel
            </Button>
            <Button type="submit" isLoading={addLocationMutation.isPending}>
              Create Location Bin
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
