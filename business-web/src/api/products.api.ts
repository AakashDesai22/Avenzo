/**
 * AVENZO Business Web — Products & Categories API Wrapper
 */

import { apiGet, apiPost, apiPut, apiDelete, apiUpload, ApiResponse } from './client';
import { Product, ProductCreate, ProductUpdate, Category, CategoryCreate, CategoryUpdate } from '../types/products';

export async function uploadImageApi(file: File, folder?: string): Promise<ApiResponse<{
  image_url: string;
  public_id: string;
  format: string;
  width: number;
  height: number;
  size_bytes: number;
}>> {
  const formData = new FormData();
  formData.append('file', file);
  const path = folder ? `/uploads/image?folder=${encodeURIComponent(folder)}` : '/uploads/image';
  return apiUpload(path, formData);
}

export async function getProductsApi(params?: {
  search?: string;
  category_id?: string;
  is_active?: boolean;
  is_published?: boolean;
  skip?: number;
  limit?: number;
}): Promise<ApiResponse<Product[]>> {
  return apiGet<Product[]>('/products', params);
}

export async function getProductByIdApi(id: string): Promise<ApiResponse<Product>> {
  return apiGet<Product>(`/products/${id}`);
}

export async function createProductApi(data: ProductCreate): Promise<ApiResponse<Product>> {
  return apiPost<Product>('/products', data);
}

export async function updateProductApi(id: string, data: ProductUpdate): Promise<ApiResponse<Product>> {
  return apiPut<Product>(`/products/${id}`, data);
}

export async function deleteProductApi(id: string): Promise<ApiResponse<Product>> {
  return apiDelete<Product>(`/products/${id}`);
}

export async function getCategoriesApi(): Promise<ApiResponse<Category[]>> {
  return apiGet<Category[]>('/categories');
}

export async function createCategoryApi(data: CategoryCreate): Promise<ApiResponse<Category>> {
  return apiPost<Category>('/categories', data);
}

export async function updateCategoryApi(id: string, data: CategoryUpdate): Promise<ApiResponse<Category>> {
  return apiPut<Category>(`/categories/${id}`, data);
}

export async function deleteCategoryApi(id: string): Promise<ApiResponse<Category>> {
  return apiDelete<Category>(`/categories/${id}`);
}

export async function publishProductApi(id: string): Promise<ApiResponse<Product>> {
  return apiPost<Product>(`/products/${id}/publish`);
}

export async function unpublishProductApi(id: string): Promise<ApiResponse<Product>> {
  return apiPost<Product>(`/products/${id}/unpublish`);
}
