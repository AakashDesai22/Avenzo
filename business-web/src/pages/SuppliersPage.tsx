/**
 * AVENZO Business Web — Supplier Management Page
 * Allows inventory and business managers to maintain master supplier records,
 * view contact details, and link suppliers during incoming batch receiving.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSuppliersApi, createSupplierApi } from '../api/suppliers.api';
import { Supplier } from '../types/suppliers';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { useAuth } from '../context/AuthContext';
import { Plus, Truck, Mail, Phone, MapPin } from 'lucide-react';

export const SuppliersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const canManage = hasRole(['ADMIN', 'BUSINESS_MANAGER']);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [contactPerson, setContactPerson] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [country, setCountry] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data: suppliersRes, isLoading } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => getSuppliersApi(),
  });

  const createMutation = useMutation({
    mutationFn: (data: {
      name: string;
      contact_person?: string;
      email?: string;
      phone?: string;
      address?: string;
      city?: string;
      country?: string;
    }) => createSupplierApi(data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['suppliers'] });
        queryClient.invalidateQueries({ queryKey: ['suppliersAll'] });
        closeModal();
      } else {
        setFormError(res.error?.message || 'Failed to create supplier.');
      }
    },
    onError: (err: any) => {
      setFormError(err.message || 'An unexpected error occurred.');
    },
  });

  const closeModal = () => {
    setIsModalOpen(false);
    setName('');
    setContactPerson('');
    setEmail('');
    setPhone('');
    setAddress('');
    setCity('');
    setCountry('');
    setFormError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!name.trim()) {
      setFormError('Supplier Name is required.');
      return;
    }

    createMutation.mutate({
      name: name.trim(),
      contact_person: contactPerson.trim() || undefined,
      email: email.trim() || undefined,
      phone: phone.trim() || undefined,
      address: address.trim() || undefined,
      city: city.trim() || undefined,
      country: country.trim() || undefined,
    });
  };

  const columns: Column<Supplier>[] = [
    {
      key: 'name',
      header: 'Supplier Name',
      render: (s) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-sm)',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-primary)',
            }}
          >
            <Truck size={16} />
          </div>
          <div>
            <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{s.name}</div>
            {s.contact_person && (
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                Contact: {s.contact_person}
              </div>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'contact',
      header: 'Contact Info',
      render: (s) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.8125rem' }}>
          {s.email && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--color-text-secondary)' }}>
              <Mail size={13} /> {s.email}
            </span>
          )}
          {s.phone && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', color: 'var(--color-text-secondary)' }}>
              <Phone size={13} /> {s.phone}
            </span>
          )}
          {!s.email && !s.phone && <span style={{ color: 'var(--color-text-muted)' }}>No contact info</span>}
        </div>
      ),
    },
    {
      key: 'location',
      header: 'Location',
      render: (s) => {
        const parts = [s.city, s.country].filter(Boolean);
        return parts.length > 0 ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.8125rem' }}>
            <MapPin size={13} color="var(--color-text-secondary)" /> {parts.join(', ')}
          </span>
        ) : (
          <span style={{ color: 'var(--color-text-muted)', fontSize: '0.8125rem' }}>N/A</span>
        );
      },
    },
    {
      key: 'status',
      header: 'Status',
      render: (s) =>
        s.is_active ? <Badge variant="success">Active</Badge> : <Badge variant="neutral">Inactive</Badge>,
    },
  ];

  return (
    <div>
      <Header
        title="Supplier Management"
        subtitle="Manage certified suppliers, distributors, and farms for batch receiving"
        action={
          canManage ? (
            <Button onClick={() => setIsModalOpen(true)}>
              <Plus size={18} /> Add Supplier
            </Button>
          ) : null
        }
      />

      <div style={{ padding: '2rem' }}>
        <Table
          columns={columns}
          data={suppliersRes?.data || []}
          keyExtractor={(s) => s.id}
          isLoading={isLoading}
        />
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title="Add New Supplier"
        subtitle="Record vendor or factory details to receive product shipments"
      >
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {formError && (
            <div
              style={{
                padding: '0.75rem',
                backgroundColor: 'var(--color-danger-bg)',
                color: '#fca5a5',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.875rem',
              }}
            >
              {formError}
            </div>
          )}

          <Input
            label="Supplier / Vendor Name *"
            placeholder="e.g., Organic Farms Co."
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input
              label="Contact Person"
              placeholder="e.g., Jane Doe"
              value={contactPerson}
              onChange={(e) => setContactPerson(e.target.value)}
            />
            <Input
              label="Phone Number"
              placeholder="+1-555-0199"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          <Input
            label="Email Address"
            type="email"
            placeholder="orders@organicfarms.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <Input
            label="Physical Address"
            placeholder="123 Harvest Road"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input
              label="City"
              placeholder="Austin"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
            <Input
              label="Country"
              placeholder="USA"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="outline" onClick={closeModal} disabled={createMutation.isPending}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending} disabled={createMutation.isPending}>
              Save Supplier
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
