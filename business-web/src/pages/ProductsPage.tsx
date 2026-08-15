import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProductsApi, createProductApi, updateProductApi, getCategoriesApi } from '../api/products.api';
import { Product, ProductCreate } from '../types/products';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { formatCurrency } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { Plus, Search } from 'lucide-react';

export const ProductsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const canManage = hasRole(['ADMIN', 'BUSINESS_MANAGER']);

  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [sku, setSku] = useState('');
  const [barcode, setBarcode] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [unitPrice, setUnitPrice] = useState('');
  const [costPrice, setCostPrice] = useState('');
  const [shelfLifeDays, setShelfLifeDays] = useState('');
  const [hasExpiry, setHasExpiry] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: productsRes, isLoading } = useQuery({
    queryKey: ['products', search, selectedCategory],
    queryFn: () => getProductsApi({ search: search || undefined, category_id: selectedCategory || undefined }),
  });

  const { data: categoriesRes } = useQuery({
    queryKey: ['categories'],
    queryFn: () => getCategoriesApi(),
  });

  const createMutation = useMutation({
    mutationFn: (data: ProductCreate) => createProductApi(data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['products'] });
        closeModal();
      } else {
        setFormError(res.error?.message || 'Failed to create product.');
      }
    },
    onError: (err: any) => {
      setFormError(err.message || 'An error occurred.');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateProductApi(id, data),
    onSuccess: (res) => {
      if (res.success) {
        queryClient.invalidateQueries({ queryKey: ['products'] });
        closeModal();
      } else {
        setFormError(res.error?.message || 'Failed to update product.');
      }
    },
  });

  const closeModal = () => {
    setIsCreateModalOpen(false);
    setEditingProduct(null);
    setName('');
    setSku('');
    setBarcode('');
    setCategoryId('');
    setUnitPrice('');
    setCostPrice('');
    setShelfLifeDays('');
    setHasExpiry(true);
    setFormError(null);
  };

  const handleOpenCreate = () => {
    setEditingProduct(null);
    if (categoriesRes?.data && categoriesRes.data.length > 0) {
      setCategoryId(categoriesRes.data[0].id);
    }
    setIsCreateModalOpen(true);
  };

  const handleOpenEdit = (prod: Product) => {
    setEditingProduct(prod);
    setName(prod.name);
    setSku(prod.sku);
    setBarcode(prod.barcode || '');
    setCategoryId(prod.category_id);
    setUnitPrice(String(prod.unit_price));
    setCostPrice(prod.cost_price ? String(prod.cost_price) : '');
    setShelfLifeDays(prod.shelf_life_days ? String(prod.shelf_life_days) : '');
    setHasExpiry(prod.has_expiry);
    setIsCreateModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!name || !sku || !categoryId || !unitPrice) {
      setFormError('Please fill in all required fields.');
      return;
    }

    if (editingProduct) {
      updateMutation.mutate({
        id: editingProduct.id,
        data: {
          name,
          barcode: barcode || undefined,
          category_id: categoryId,
          unit_price: parseFloat(unitPrice),
          cost_price: costPrice ? parseFloat(costPrice) : undefined,
          shelf_life_days: shelfLifeDays ? parseInt(shelfLifeDays, 10) : undefined,
          has_expiry: hasExpiry,
        },
      });
    } else {
      createMutation.mutate({
        name,
        sku,
        barcode: barcode || undefined,
        category_id: categoryId,
        unit_price: parseFloat(unitPrice),
        cost_price: costPrice ? parseFloat(costPrice) : undefined,
        shelf_life_days: shelfLifeDays ? parseInt(shelfLifeDays, 10) : undefined,
        has_expiry: hasExpiry,
      });
    }
  };

  const columns: Column<Product>[] = [
    { key: 'name', header: 'Product Name', render: (p) => <span style={{ fontWeight: 600 }}>{p.name}</span> },
    { key: 'sku', header: 'SKU' },
    { key: 'category', header: 'Category', render: (p) => p.category?.name || 'N/A' },
    { key: 'unit_price', header: 'Unit Price', render: (p) => formatCurrency(p.unit_price) },
    { key: 'cost_price', header: 'Cost Price', render: (p) => formatCurrency(p.cost_price) },
    { key: 'shelf_life', header: 'Shelf Life', render: (p) => (p.shelf_life_days ? `${p.shelf_life_days} days` : 'N/A') },
    {
      key: 'has_expiry',
      header: 'Expiry Tracking',
      render: (p) => (p.has_expiry ? <Badge variant="success">Enabled</Badge> : <Badge variant="neutral">Disabled</Badge>),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (p) =>
        canManage ? (
          <Button size="sm" variant="outline" onClick={() => handleOpenEdit(p)}>
            Edit
          </Button>
        ) : null,
    },
  ];

  return (
    <div>
      <Header
        title="Product Catalogue"
        subtitle="Manage master product records, SKUs, and pricing"
        action={
          canManage ? (
            <Button onClick={handleOpenCreate}>
              <Plus size={18} /> Add Product
            </Button>
          ) : null
        }
      />

      <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Search & Filter Bar */}
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '240px', position: 'relative' }}>
            <Input
              placeholder="Search by product name or SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{
              padding: '0.625rem 1rem',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-primary)',
            }}
          >
            <option value="">All Categories</option>
            {categoriesRes?.data?.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </div>

        {/* Product Data Table */}
        <Table columns={columns} data={productsRes?.data || []} keyExtractor={(p) => p.id} isLoading={isLoading} />
      </div>

      {/* Product Create/Edit Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={closeModal}
        title={editingProduct ? 'Edit Product' : 'Add New Product'}
        subtitle={editingProduct ? `Updating SKU: ${editingProduct.sku}` : 'Create a new product in catalogue'}
      >
        <form id="product-form" onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {formError && (
            <div style={{ padding: '0.75rem', backgroundColor: 'var(--color-danger-bg)', color: '#fca5a5', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
              {formError}
            </div>
          )}

          <Input label="Product Name *" value={name} onChange={(e) => setName(e.target.value)} required />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input label="SKU *" value={sku} onChange={(e) => setSku(e.target.value)} disabled={!!editingProduct} required />
            <Input label="Barcode" value={barcode} onChange={(e) => setBarcode(e.target.value)} />
          </div>

          <div>
            <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', display: 'block', marginBottom: '0.375rem' }}>
              Category *
            </label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              required
              style={{
                width: '100%',
                padding: '0.625rem',
                backgroundColor: 'var(--color-surface)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--color-text-primary)',
              }}
            >
              {categoriesRes?.data?.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input label="Unit Selling Price (₹) *" type="number" step="0.01" value={unitPrice} onChange={(e) => setUnitPrice(e.target.value)} required />
            <Input label="Cost Price (₹)" type="number" step="0.01" value={costPrice} onChange={(e) => setCostPrice(e.target.value)} />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input label="Shelf Life (Days)" type="number" value={shelfLifeDays} onChange={(e) => setShelfLifeDays(e.target.value)} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', justifyContent: 'center' }}>
              <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>Has Expiry Date?</label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.875rem' }}>
                <input type="checkbox" checked={hasExpiry} onChange={(e) => setHasExpiry(e.target.checked)} />
                Enable Expiry Tracking
              </label>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button type="button" variant="secondary" onClick={closeModal}>
              Cancel
            </Button>
            <Button type="submit" isLoading={createMutation.isPending || updateMutation.isPending}>
              {editingProduct ? 'Update Product' : 'Create Product'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
