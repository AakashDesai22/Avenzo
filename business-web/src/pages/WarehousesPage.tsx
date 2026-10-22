/**
 * AVENZO Business Web — Warehouse Facilities Management Page
 * Multi-facility management, bin locations, facility creation, editing, and integrity-safe deactivation.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getWarehousesApi,
  createWarehouseApi,
  updateWarehouseApi,
  deactivateWarehouseApi,
  createWarehouseLocationApi,
} from '../api/inventory.api';
import { Warehouse, WarehouseCreate, WarehouseUpdate } from '../types/inventory';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { useAuth } from '../context/AuthContext';
import {
  Building2,
  MapPin,
  Plus,
  Box,
  Edit2,
  Trash2,
  CheckCircle,
  AlertCircle,
  Search,
} from 'lucide-react';

export const WarehousesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const canManage = hasRole(['ADMIN', 'BUSINESS_MANAGER']);

  // Search & Filter
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActiveOnly, setFilterActiveOnly] = useState(false);

  // Warehouse Create/Edit Modal State
  const [isWarehouseModalOpen, setIsWarehouseModalOpen] = useState(false);
  const [editingWarehouse, setEditingWarehouse] = useState<Warehouse | null>(null);
  const [whName, setWhName] = useState('');
  const [whCity, setWhCity] = useState('');
  const [whAddress, setWhAddress] = useState('');
  const [whIsActive, setWhIsActive] = useState(true);
  const [whFormError, setWhFormError] = useState<string | null>(null);

  // Location Bin Modal State
  const [selectedWarehouseForBin, setSelectedWarehouseForBin] = useState<string | null>(null);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [locationCode, setLocationCode] = useState('');
  const [locationDesc, setLocationDesc] = useState('');
  const [locFormError, setLocFormError] = useState<string | null>(null);

  // Global Action Notification (for deactivation or save feedback)
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Fetch Warehouses
  const { data: warehousesRes, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['warehousesOverview', filterActiveOnly],
    queryFn: () => getWarehousesApi({ active_only: filterActiveOnly }),
  });

  // Create Warehouse Mutation
  const createWarehouseMutation = useMutation({
    mutationFn: (data: WarehouseCreate) => createWarehouseApi(data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['warehousesOverview'] });
        queryClient.invalidateQueries({ queryKey: ['warehouses'] });
        queryClient.invalidateQueries({ queryKey: ['warehousesAll'] });
        closeWarehouseModal();
        setActionFeedback({ type: 'success', message: 'Warehouse created successfully.' });
      } else {
        setWhFormError(res.error?.message || 'Failed to create warehouse.');
      }
    },
    onError: (err: any) => {
      setWhFormError(err.message || 'An unexpected error occurred while creating warehouse.');
    },
  });

  // Update Warehouse Mutation
  const updateWarehouseMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: WarehouseUpdate }) => updateWarehouseApi(id, data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['warehousesOverview'] });
        queryClient.invalidateQueries({ queryKey: ['warehouses'] });
        queryClient.invalidateQueries({ queryKey: ['warehousesAll'] });
        closeWarehouseModal();
        setActionFeedback({ type: 'success', message: 'Warehouse updated successfully.' });
      } else {
        setWhFormError(res.error?.message || 'Failed to update warehouse.');
      }
    },
    onError: (err: any) => {
      setWhFormError(err.message || 'An unexpected error occurred while updating warehouse.');
    },
  });

  // Deactivate Warehouse Mutation
  const deactivateWarehouseMutation = useMutation({
    mutationFn: (id: string) => deactivateWarehouseApi(id),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['warehousesOverview'] });
        queryClient.invalidateQueries({ queryKey: ['warehouses'] });
        queryClient.invalidateQueries({ queryKey: ['warehousesAll'] });
        setActionFeedback({ type: 'success', message: 'Warehouse facility deactivated.' });
      } else {
        setActionFeedback({ type: 'error', message: res.error?.message || 'Failed to deactivate warehouse.' });
      }
    },
    onError: (err: any) => {
      setActionFeedback({
        type: 'error',
        message: err.message || 'Cannot deactivate warehouse with active inventory balances.',
      });
    },
  });

  // Add Bin Location Mutation
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
        setActionFeedback({ type: 'success', message: 'Location bin created successfully.' });
      } else {
        setLocFormError(res.error?.message || 'Failed to add location bin.');
      }
    },
    onError: (err: any) => {
      setLocFormError(err.message || 'Failed to add location bin.');
    },
  });

  const closeWarehouseModal = () => {
    setIsWarehouseModalOpen(false);
    setEditingWarehouse(null);
    setWhName('');
    setWhCity('');
    setWhAddress('');
    setWhIsActive(true);
    setWhFormError(null);
  };

  const handleOpenCreateWarehouse = () => {
    setEditingWarehouse(null);
    setWhName('');
    setWhCity('');
    setWhAddress('');
    setWhIsActive(true);
    setWhFormError(null);
    setIsWarehouseModalOpen(true);
  };

  const handleOpenEditWarehouse = (wh: Warehouse) => {
    setEditingWarehouse(wh);
    setWhName(wh.name);
    setWhCity(wh.city || '');
    setWhAddress(wh.address || '');
    setWhIsActive(wh.is_active);
    setWhFormError(null);
    setIsWarehouseModalOpen(true);
  };

  const handleWarehouseSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setWhFormError(null);

    if (!whName.trim()) {
      setWhFormError('Warehouse name is required.');
      return;
    }

    if (editingWarehouse) {
      updateWarehouseMutation.mutate({
        id: editingWarehouse.id,
        data: {
          name: whName.trim(),
          city: whCity.trim() || undefined,
          address: whAddress.trim() || undefined,
          is_active: whIsActive,
        },
      });
    } else {
      createWarehouseMutation.mutate({
        name: whName.trim(),
        city: whCity.trim() || undefined,
        address: whAddress.trim() || undefined,
        is_active: true,
      });
    }
  };

  const closeLocationModal = () => {
    setIsLocationModalOpen(false);
    setSelectedWarehouseForBin(null);
    setLocationCode('');
    setLocationDesc('');
    setLocFormError(null);
  };

  const handleOpenAddLocation = (whId: string) => {
    setSelectedWarehouseForBin(whId);
    setIsLocationModalOpen(true);
  };

  const handleAddLocationSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLocFormError(null);

    if (!locationCode.trim() || !selectedWarehouseForBin) {
      setLocFormError('Location bin code is required.');
      return;
    }

    addLocationMutation.mutate({
      warehouseId: selectedWarehouseForBin,
      code: locationCode.trim(),
      desc: locationDesc.trim() || undefined,
    });
  };

  const handleDeactivate = (wh: Warehouse) => {
    if (
      window.confirm(
        `Are you sure you want to deactivate warehouse "${wh.name}"? This is only permitted if the warehouse has zero active inventory.`
      )
    ) {
      deactivateWarehouseMutation.mutate(wh.id);
    }
  };

  const handleReactivate = (wh: Warehouse) => {
    updateWarehouseMutation.mutate({
      id: wh.id,
      data: { is_active: true },
    });
  };

  const allWarehouses = warehousesRes?.data || [];
  const filteredWarehouses = allWarehouses.filter((wh) => {
    const matchesSearch =
      wh.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (wh.city && wh.city.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (wh.address && wh.address.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesSearch;
  });

  return (
    <div>
      <Header
        title="Warehouse Facilities"
        subtitle="Multi-facility oversight, storage bins, and physical location management"
        action={
          canManage ? (
            <Button onClick={handleOpenCreateWarehouse}>
              <Plus size={18} /> Add Warehouse
            </Button>
          ) : null
        }
      />

      <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {/* Action Feedback Notification */}
        {actionFeedback && (
          <div
            style={{
              padding: '0.875rem 1rem',
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor:
                actionFeedback.type === 'success'
                  ? 'rgba(34, 197, 94, 0.1)'
                  : 'var(--color-danger-bg, rgba(239, 68, 68, 0.1))',
              color: actionFeedback.type === 'success' ? '#22c55e' : '#f87171',
              border: `1px solid ${
                actionFeedback.type === 'success' ? 'rgba(34, 197, 94, 0.25)' : 'rgba(239, 68, 68, 0.25)'
              }`,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
              {actionFeedback.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
              <span>{actionFeedback.message}</span>
            </div>
            <button
              onClick={() => setActionFeedback(null)}
              style={{
                background: 'none',
                border: 'none',
                color: 'inherit',
                cursor: 'pointer',
                fontSize: '0.875rem',
                opacity: 0.8,
              }}
            >
              ✕
            </button>
          </div>
        )}

        {/* Search and Filters Bar */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            flexWrap: 'wrap',
          }}
        >
          <div style={{ position: 'relative', width: '320px', maxWidth: '100%' }}>
            <Search
              size={16}
              style={{
                position: 'absolute',
                left: '0.75rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--color-text-muted)',
              }}
            />
            <input
              type="text"
              placeholder="Search by facility name, city, or address..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '0.625rem 0.75rem 0.625rem 2.25rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-surface)',
                color: 'var(--color-text-primary)',
                fontSize: '0.875rem',
              }}
            />
          </div>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.875rem',
              color: 'var(--color-text-secondary)',
              cursor: 'pointer',
            }}
          >
            <input
              type="checkbox"
              checked={filterActiveOnly}
              onChange={(e) => setFilterActiveOnly(e.target.checked)}
            />
            Show active facilities only
          </label>
        </div>

        {/* Facilities Grid or Empty State */}
        {isLoading ? (
          <div
            style={{
              padding: '4rem 2rem',
              textAlign: 'center',
              backgroundColor: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-muted)',
            }}
          >
            Loading warehouse facilities...
          </div>
        ) : isError || (warehousesRes && !warehousesRes.success) ? (
          <div
            style={{
              padding: '3rem 2rem',
              textAlign: 'center',
              backgroundColor: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '1rem',
            }}
          >
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                color: '#ef4444',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <AlertCircle size={28} />
            </div>
            <div>
              <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.125rem', color: 'var(--color-text-primary)' }}>
                Unable to load warehouse facilities
              </h3>
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary)', maxWidth: '420px' }}>
                {warehousesRes?.error?.message || (error as Error)?.message || 'Failed to communicate with warehouse service.'}
              </p>
            </div>
            <Button variant="secondary" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        ) : filteredWarehouses.length === 0 ? (
          <div
            style={{
              padding: '4rem 2rem',
              textAlign: 'center',
              backgroundColor: 'var(--color-surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '1rem',
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                color: '#3b82f6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Building2 size={32} />
            </div>
            <div>
              <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.25rem', color: 'var(--color-text-primary)' }}>
                {searchTerm ? 'No matching facilities found' : 'No warehouse facilities configured'}
              </h3>
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary)', maxWidth: '420px' }}>
                {searchTerm
                  ? 'Try searching with a different facility name or clear your filters.'
                  : 'Get started by creating your primary storage facility or distribution center.'}
              </p>
            </div>
            {canManage ? (
              <Button onClick={handleOpenCreateWarehouse} style={{ marginTop: '0.5rem' }}>
                <Plus size={18} /> Create First Warehouse
              </Button>
            ) : (
              <p style={{ margin: '0.5rem 0 0', fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>
                You have read-only access. Contact an administrator to register warehouse facilities.
              </p>
            )}
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
              gap: '1.5rem',
            }}
          >
            {filteredWarehouses.map((wh) => (
              <div
                key={wh.id}
                style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '1.5rem',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: '1.25rem',
                  boxShadow: 'var(--shadow-sm)',
                }}
              >
                <div>
                  {/* Warehouse Header */}
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      marginBottom: '0.75rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <div
                        style={{
                          width: 44,
                          height: 44,
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: wh.is_active ? 'rgba(59, 130, 246, 0.1)' : 'rgba(148, 163, 184, 0.1)',
                          color: wh.is_active ? '#3b82f6' : '#94a3b8',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                        }}
                      >
                        <Building2 size={24} />
                      </div>
                      <div>
                        <h3
                          style={{
                            fontSize: '1.125rem',
                            fontWeight: 700,
                            color: 'var(--color-text-primary)',
                            margin: 0,
                          }}
                        >
                          {wh.name}
                        </h3>
                        <p
                          style={{
                            fontSize: '0.75rem',
                            color: 'var(--color-text-muted)',
                            margin: '0.125rem 0 0',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                          }}
                        >
                          <MapPin size={12} />
                          {wh.city ? `${wh.address || 'Facility'}, ${wh.city}` : wh.address || 'Primary Logistics Hub'}
                        </p>
                      </div>
                    </div>
                    <Badge variant={wh.is_active ? 'success' : 'neutral'}>
                      {wh.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </Badge>
                  </div>

                  {/* Storage Bins Section */}
                  <div
                    style={{
                      marginTop: '1rem',
                      borderTop: '1px solid var(--color-border)',
                      paddingTop: '1rem',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: '0.625rem',
                      }}
                    >
                      <span
                        style={{
                          fontSize: '0.8125rem',
                          fontWeight: 600,
                          color: 'var(--color-text-secondary)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.375rem',
                        }}
                      >
                        <Box size={14} /> Storage Bins ({wh.locations?.length || 0})
                      </span>
                      {canManage && wh.is_active && (
                        <button
                          onClick={() => handleOpenAddLocation(wh.id)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#3b82f6',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            padding: '0.25rem 0.5rem',
                            borderRadius: 'var(--radius-sm)',
                          }}
                        >
                          <Plus size={12} /> Add Bin
                        </button>
                      )}
                    </div>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem', minHeight: '32px' }}>
                      {wh.locations && wh.locations.length > 0 ? (
                        wh.locations.map((loc) => (
                          <span
                            key={loc.id}
                            style={{
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              padding: '0.25rem 0.5rem',
                              backgroundColor: 'var(--color-border-subtle, rgba(255,255,255,0.04))',
                              borderRadius: 'var(--radius-sm)',
                              color: 'var(--color-text-primary)',
                              border: '1px solid var(--color-border)',
                            }}
                            title={loc.description || undefined}
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

                {/* Warehouse Footer & Actions */}
                <div
                  style={{
                    borderTop: '1px solid var(--color-border)',
                    paddingTop: '0.875rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
                    <span>ID: {wh.id.substring(0, 8)}...</span>
                  </div>

                  {canManage && (
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <Button size="sm" variant="outline" onClick={() => handleOpenEditWarehouse(wh)}>
                        <Edit2 size={13} style={{ marginRight: '0.25rem' }} /> Edit
                      </Button>

                      {wh.is_active ? (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleDeactivate(wh)}
                          isLoading={deactivateWarehouseMutation.isPending}
                          title="Deactivate warehouse facility (only allowed if stock is empty)"
                        >
                          <Trash2 size={13} style={{ marginRight: '0.25rem' }} /> Deactivate
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleReactivate(wh)}
                          isLoading={updateWarehouseMutation.isPending}
                        >
                          Reactivate
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create / Edit Warehouse Modal */}
      <Modal
        isOpen={isWarehouseModalOpen}
        onClose={closeWarehouseModal}
        title={editingWarehouse ? 'Edit Warehouse Facility' : 'Create New Warehouse'}
        subtitle={editingWarehouse ? `Editing facility: ${editingWarehouse.name}` : 'Register a new storage and fulfillment facility'}
      >
        <form onSubmit={handleWarehouseSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {whFormError && (
            <div
              style={{
                padding: '0.75rem',
                backgroundColor: 'var(--color-danger-bg, rgba(239, 68, 68, 0.1))',
                color: '#f87171',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.875rem',
              }}
            >
              {whFormError}
            </div>
          )}

          <Input
            label="Warehouse Facility Name *"
            placeholder="e.g. Central Distribution Hub"
            value={whName}
            onChange={(e) => setWhName(e.target.value)}
            required
          />

          <Input
            label="City / Region"
            placeholder="e.g. Mumbai, Navi Mumbai, Pune"
            value={whCity}
            onChange={(e) => setWhCity(e.target.value)}
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
              value={whAddress}
              onChange={(e) => setWhAddress(e.target.value)}
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

          {editingWarehouse && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.875rem' }}>
                <input
                  type="checkbox"
                  checked={whIsActive}
                  onChange={(e) => setWhIsActive(e.target.checked)}
                />
                Facility Active Status
              </label>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={closeWarehouseModal}>
              Cancel
            </Button>
            <Button
              type="submit"
              isLoading={createWarehouseMutation.isPending || updateWarehouseMutation.isPending}
            >
              {editingWarehouse ? 'Save Changes' : 'Create Warehouse'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Location Bin Modal */}
      <Modal
        isOpen={isLocationModalOpen}
        onClose={closeLocationModal}
        title="Add Storage Bin Location"
        subtitle="Create an aisle, rack, or bin identifier within the facility"
      >
        <form onSubmit={handleAddLocationSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {locFormError && (
            <div
              style={{
                padding: '0.75rem',
                backgroundColor: 'var(--color-danger-bg, rgba(239, 68, 68, 0.1))',
                color: '#f87171',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.875rem',
              }}
            >
              {locFormError}
            </div>
          )}

          <Input
            label="Bin Location Code *"
            placeholder="e.g. AISLE-A1-BIN04"
            value={locationCode}
            onChange={(e) => setLocationCode(e.target.value)}
            required
          />

          <Input
            label="Description (Optional)"
            placeholder="e.g. Cold storage shelf A1"
            value={locationDesc}
            onChange={(e) => setLocationDesc(e.target.value)}
          />

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
