import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getCategoriesApi, createCategoryApi } from '../api/products.api';
import { Category } from '../types/products';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { useAuth } from '../context/AuthContext';
import { Plus } from 'lucide-react';

export const CategoriesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const canManage = hasRole(['ADMIN', 'BUSINESS_MANAGER']);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data: categoriesRes, isLoading } = useQuery({
    queryKey: ['categories'],
    queryFn: () => getCategoriesApi(),
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description?: string }) => createCategoryApi(data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['categories'] });
        closeModal();
      } else {
        setFormError(res.error?.message || 'Failed to create category.');
      }
    },
  });

  const closeModal = () => {
    setIsModalOpen(false);
    setName('');
    setDescription('');
    setFormError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) {
      setFormError('Category name is required.');
      return;
    }
    createMutation.mutate({ name, description: description || undefined });
  };

  const columns: Column<Category>[] = [
    { key: 'name', header: 'Category Name', render: (c) => <span style={{ fontWeight: 600 }}>{c.name}</span> },
    { key: 'description', header: 'Description', render: (c) => c.description || 'N/A' },
    {
      key: 'status',
      header: 'Status',
      render: (c) => (c.is_active ? <Badge variant="success">Active</Badge> : <Badge variant="neutral">Inactive</Badge>),
    },
  ];

  return (
    <div>
      <Header
        title="Product Categories"
        subtitle="Manage product category hierarchy"
        action={
          canManage ? (
            <Button onClick={() => setIsModalOpen(true)}>
              <Plus size={18} /> Add Category
            </Button>
          ) : null
        }
      />

      <div style={{ padding: '2rem' }}>
        <Table columns={columns} data={categoriesRes?.data || []} keyExtractor={(c) => c.id} isLoading={isLoading} />
      </div>

      <Modal isOpen={isModalOpen} onClose={closeModal} title="Add New Category">
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {formError && (
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--color-danger-bg)', color: '#fca5a5', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
              {formError}
            </div>
          )}

          <Input label="Category Name *" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Description" value={description} onChange={(e) => setDescription(e.target.value)} />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={closeModal}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending}>
              Create Category
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
