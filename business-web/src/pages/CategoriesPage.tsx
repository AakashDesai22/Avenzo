import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getCategoriesApi,
  createCategoryApi,
  updateCategoryApi,
  deleteCategoryApi,
} from '../api/products.api';
import { Category, CategoryCreate, CategoryUpdate } from '../types/products';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { ImageUpload } from '../components/ui/ImageUpload';
import { useAuth } from '../context/AuthContext';
import { Plus, Tags } from 'lucide-react';

export const CategoriesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const canManage = hasRole(['ADMIN', 'BUSINESS_MANAGER']);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  // Fetch all categories (including inactive) for admin view
  const { data: categoriesRes, isLoading } = useQuery({
    queryKey: ['categories', 'all'],
    queryFn: () => getCategoriesApi(),
  });

  const createMutation = useMutation({
    mutationFn: (data: CategoryCreate) => createCategoryApi(data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['categories'] });
        closeModal();
      } else {
        setFormError(res.error?.message || 'Failed to create category.');
      }
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: CategoryUpdate }) =>
      updateCategoryApi(id, data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['categories'] });
        closeModal();
      } else {
        setFormError(res.error?.message || 'Failed to update category.');
      }
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => deleteCategoryApi(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['categories'] }),
  });

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingCategory(null);
    setName('');
    setDescription('');
    setImageUrl('');
    setFormError(null);
  };

  const handleOpenCreate = () => {
    setEditingCategory(null);
    setName('');
    setDescription('');
    setImageUrl('');
    setIsModalOpen(true);
  };

  const handleOpenEdit = (cat: Category) => {
    setEditingCategory(cat);
    setName(cat.name);
    setDescription(cat.description || '');
    setImageUrl(cat.image_url || '');
    setIsModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setFormError('Category name is required.');
      return;
    }

    if (editingCategory) {
      updateMutation.mutate({
        id: editingCategory.id,
        data: { name: name.trim(), description: description.trim() || undefined, image_url: imageUrl ? imageUrl : null },
      });
    } else {
      createMutation.mutate({
        name: name.trim(),
        description: description.trim() || undefined,
        image_url: imageUrl || undefined,
      });
    }
  };

  const columns: Column<Category>[] = [
    {
      key: 'name',
      header: 'Category Name',
      render: (c) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 'var(--radius-sm)',
              overflow: 'hidden',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {c.image_url ? (
              <img
                src={c.image_url}
                alt={c.name}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).style.display = 'none';
                }}
              />
            ) : (
              <Tags size={18} color="var(--color-text-secondary)" />
            )}
          </div>
          <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{c.name}</span>
        </div>
      ),
    },
    { key: 'description', header: 'Description', render: (c) => c.description || 'N/A' },
    {
      key: 'status',
      header: 'Status',
      render: (c) =>
        c.is_active ? <Badge variant="success">Active</Badge> : <Badge variant="neutral">Inactive</Badge>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (c) =>
        canManage ? (
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Button size="sm" variant="outline" onClick={() => handleOpenEdit(c)}>
              Edit
            </Button>
            {c.is_active && (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => deactivateMutation.mutate(c.id)}
                isLoading={deactivateMutation.isPending}
              >
                Deactivate
              </Button>
            )}
          </div>
        ) : null,
    },
  ];

  return (
    <div>
      <Header
        title="Product Categories"
        subtitle="Manage product category hierarchy"
        action={
          canManage ? (
            <Button onClick={handleOpenCreate}>
              <Plus size={18} /> Add Category
            </Button>
          ) : null
        }
      />

      <div style={{ padding: '2rem' }}>
        <Table
          columns={columns}
          data={categoriesRes?.data || []}
          keyExtractor={(c) => c.id}
          isLoading={isLoading}
        />
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={closeModal}
        title={editingCategory ? 'Edit Category' : 'Add New Category'}
        subtitle={editingCategory ? `Editing: ${editingCategory.name}` : undefined}
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

          <Input label="Category Name *" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <ImageUpload
            label="Category Icon / Image"
            value={imageUrl}
            onChange={setImageUrl}
            aspectRatio="square"
            helperText="Square icon (JPEG, PNG, WebP max 5 MB)"
          />

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={closeModal}>
              Cancel
            </Button>
            <Button
              type="submit"
              isLoading={createMutation.isPending || updateMutation.isPending}
            >
              {editingCategory ? 'Update Category' : 'Create Category'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
