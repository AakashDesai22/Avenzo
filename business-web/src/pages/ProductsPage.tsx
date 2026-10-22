import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getProductsApi,
  createProductApi,
  updateProductApi,
  getCategoriesApi,
  publishProductApi,
  unpublishProductApi,
} from '../api/products.api';
import { Product, ProductCreate } from '../types/products';
import { Header } from '../components/layout/Header';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Table, Column } from '../components/ui/Table';
import { Modal } from '../components/ui/Modal';
import { Badge } from '../components/ui/Badge';
import { ImageUpload } from '../components/ui/ImageUpload';
import { formatCurrency } from '../utils/formatters';
import { useAuth } from '../context/AuthContext';
import { Plus, Globe, EyeOff, Package } from 'lucide-react';

export const ProductsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { hasRole } = useAuth();
  const canManage = hasRole(['ADMIN', 'BUSINESS_MANAGER']);

  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [publishFilter, setPublishFilter] = useState<string>('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  // Form states
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sku, setSku] = useState('');
  const [barcode, setBarcode] = useState('');
  const [imageUrl, setImageUrl] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [unitPrice, setUnitPrice] = useState('');
  const [costPrice, setCostPrice] = useState('');
  const [shelfLifeDays, setShelfLifeDays] = useState('');
  const [hasExpiry, setHasExpiry] = useState(true);
  const [isPublished, setIsPublished] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: productsRes, isLoading } = useQuery({
    queryKey: ['products', search, selectedCategory, publishFilter],
    queryFn: () =>
      getProductsApi({
        search: search || undefined,
        category_id: selectedCategory || undefined,
        is_published: publishFilter !== '' ? publishFilter === 'true' : undefined,
      }),
  });

  const { data: categoriesRes } = useQuery({
    queryKey: ['categories'],
    queryFn: () => getCategoriesApi(),
  });

  useEffect(() => {
    if (!categoryId && categoriesRes?.data && categoriesRes.data.length > 0) {
      setCategoryId(categoriesRes.data[0].id);
    }
  }, [categoriesRes, categoryId]);

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

  const publishMutation = useMutation({
    mutationFn: (id: string) => publishProductApi(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['products'] }),
  });

  const unpublishMutation = useMutation({
    mutationFn: (id: string) => unpublishProductApi(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['products'] }),
  });

  const closeModal = () => {
    setIsCreateModalOpen(false);
    setEditingProduct(null);
    setName('');
    setDescription('');
    setSku('');
    setBarcode('');
    setImageUrl('');
    setCategoryId('');
    setUnitPrice('');
    setCostPrice('');
    setShelfLifeDays('');
    setHasExpiry(true);
    setIsPublished(false);
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
    setDescription(prod.description || '');
    setSku(prod.sku);
    setBarcode(prod.barcode || '');
    setImageUrl(prod.image_url || '');
    setCategoryId(prod.category_id);
    setUnitPrice(String(prod.unit_price));
    setCostPrice(prod.cost_price ? String(prod.cost_price) : '');
    setShelfLifeDays(prod.shelf_life_days ? String(prod.shelf_life_days) : '');
    setHasExpiry(prod.has_expiry);
    setIsPublished(prod.is_published);
    setIsCreateModalOpen(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const trimmedName = name.trim();
    const trimmedSku = sku.trim();
    const trimmedBarcode = barcode.trim();
    const trimmedDescription = description.trim();
    const trimmedImageUrl = imageUrl.trim();

    if (!trimmedName || !trimmedSku || !categoryId || !unitPrice) {
      setFormError('Please fill in all required fields.');
      return;
    }

    const parsedUnitPrice = parseFloat(unitPrice);
    if (isNaN(parsedUnitPrice) || parsedUnitPrice < 0) {
      setFormError('Please enter a valid unit selling price greater than or equal to 0.');
      return;
    }

    const parsedCostPrice = costPrice && costPrice.trim() !== '' ? parseFloat(costPrice) : undefined;
    if (parsedCostPrice !== undefined && (isNaN(parsedCostPrice) || parsedCostPrice < 0)) {
      setFormError('Cost price must be greater than or equal to 0.');
      return;
    }

    const parsedShelfLife = shelfLifeDays && shelfLifeDays.trim() !== '' ? parseInt(shelfLifeDays, 10) : undefined;
    if (parsedShelfLife !== undefined && (isNaN(parsedShelfLife) || parsedShelfLife < 0)) {
      setFormError('Shelf life must be a positive number of days.');
      return;
    }

    if (editingProduct) {
      updateMutation.mutate({
        id: editingProduct.id,
        data: {
          name: trimmedName,
          description: trimmedDescription || undefined,
          barcode: trimmedBarcode || undefined,
          category_id: categoryId,
          unit_price: parsedUnitPrice,
          cost_price: parsedCostPrice,
          shelf_life_days: parsedShelfLife,
          has_expiry: hasExpiry,
          image_url: trimmedImageUrl ? trimmedImageUrl : null,
          is_published: isPublished,
        },
      });
    } else {
      createMutation.mutate({
        name: trimmedName,
        description: trimmedDescription || undefined,
        sku: trimmedSku,
        barcode: trimmedBarcode || undefined,
        category_id: categoryId,
        unit_price: parsedUnitPrice,
        cost_price: parsedCostPrice,
        shelf_life_days: parsedShelfLife,
        has_expiry: hasExpiry,
        image_url: trimmedImageUrl || undefined,
        is_published: isPublished,
      });
    }
  };

  const columns: Column<Product>[] = [
    {
      key: 'name',
      header: 'Product',
      render: (p) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '40px',
              height: '40px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-surface-hover, rgba(255,255,255,0.05))',
              overflow: 'hidden',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
              border: '1px solid var(--color-border)',
            }}
          >
            {p.image_url ? (
              <img
                src={p.image_url}
                alt={p.name}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            ) : (
              <Package size={20} color="var(--color-text-secondary)" />
            )}
          </div>
          <div>
            <span style={{ fontWeight: 600, display: 'block' }}>{p.name}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
              SKU: {p.sku}
            </span>
          </div>
        </div>
      ),
    },
    { key: 'category', header: 'Category', render: (p) => p.category?.name || 'N/A' },
    {
      key: 'pricing',
      header: 'Price',
      render: (p) => (
        <div>
          <span style={{ fontWeight: 600, display: 'block' }}>{formatCurrency(p.unit_price)}</span>
          {p.cost_price != null && (
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
              Cost: {formatCurrency(p.cost_price)}
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'shelf_life',
      header: 'Shelf Life / Expiry',
      render: (p) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <span>{p.shelf_life_days ? `${p.shelf_life_days} days` : 'N/A'}</span>
          {p.has_expiry ? (
            <Badge variant="info">Expiry Tracked</Badge>
          ) : (
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>No Expiry</span>
          )}
        </div>
      ),
    },
    {
      key: 'is_published',
      header: 'Status',
      render: (p) =>
        p.is_published ? (
          <Badge variant="success">Published</Badge>
        ) : (
          <Badge variant="warning">Draft</Badge>
        ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (p) =>
        canManage ? (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <Button size="sm" variant="outline" onClick={() => handleOpenEdit(p)}>
              Edit
            </Button>
            {p.is_published ? (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => unpublishMutation.mutate(p.id)}
                isLoading={unpublishMutation.isPending}
                title="Revert to draft — hides from consumer marketplace"
              >
                <EyeOff size={14} /> Unpublish
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={() => publishMutation.mutate(p.id)}
                isLoading={publishMutation.isPending}
                title="Publish — makes visible in consumer marketplace"
              >
                <Globe size={14} /> Publish
              </Button>
            )}
          </div>
        ) : null,
    },
  ];

  return (
    <div>
      <Header
        title="Product Catalogue"
        subtitle="Manage master product records, SKUs, pricing, and publish to consumer marketplace"
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
          <div style={{ flex: 1, minWidth: '240px' }}>
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
          <select
            value={publishFilter}
            onChange={(e) => setPublishFilter(e.target.value)}
            style={{
              padding: '0.625rem 1rem',
              backgroundColor: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--color-text-primary)',
            }}
          >
            <option value="">All Statuses</option>
            <option value="true">Published</option>
            <option value="false">Draft</option>
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

          <Input label="Product Name *" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input
              label="SKU *"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
              disabled={!!editingProduct}
              required
            />
            <Input label="Barcode" value={barcode} onChange={(e) => setBarcode(e.target.value)} />
          </div>

          <ImageUpload
            label="Product Image"
            value={imageUrl}
            onChange={setImageUrl}
          />

          <div>
            <label
              style={{
                fontSize: '0.875rem',
                color: 'var(--color-text-secondary)',
                display: 'block',
                marginBottom: '0.375rem',
              }}
            >
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
              <option value="">Select a category...</option>
              {categoriesRes?.data?.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input
              label="Unit Selling Price (₹) *"
              type="number"
              step="0.01"
              value={unitPrice}
              onChange={(e) => setUnitPrice(e.target.value)}
              required
            />
            <Input
              label="Cost Price (₹)"
              type="number"
              step="0.01"
              value={costPrice}
              onChange={(e) => setCostPrice(e.target.value)}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input
              label="Shelf Life (Days)"
              type="number"
              value={shelfLifeDays}
              onChange={(e) => setShelfLifeDays(e.target.value)}
            />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', justifyContent: 'center' }}>
              <label style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
                Has Expiry Date?
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.875rem' }}>
                <input type="checkbox" checked={hasExpiry} onChange={(e) => setHasExpiry(e.target.checked)} />
                Enable Expiry Tracking
              </label>
            </div>
          </div>

          {/* Publish toggle */}
          <div
            style={{
              padding: '0.875rem',
              backgroundColor: isPublished ? 'rgba(34, 197, 94, 0.06)' : 'var(--color-surface-alt, rgba(0,0,0,0.04))',
              border: `1px solid ${isPublished ? 'rgba(34, 197, 94, 0.3)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <p style={{ margin: 0, fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                {isPublished ? '🟢 Published' : '⚫ Draft'}
              </p>
              <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>
                {isPublished
                  ? 'Visible to consumers in the marketplace'
                  : 'Hidden from consumers — save as draft'}
              </p>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.875rem' }}>
              <input
                type="checkbox"
                checked={isPublished}
                onChange={(e) => setIsPublished(e.target.checked)}
              />
              Publish to marketplace
            </label>
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
