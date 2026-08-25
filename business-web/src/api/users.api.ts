/**
 * AVENZO Business Web — Users & Administration API Wrapper
 */

import { apiGet, apiPost, apiPut, apiDelete, ApiResponse } from './client';
import { User, RegisterRequest } from '../types/auth';

export async function getUsersApi(): Promise<ApiResponse<User[]>> {
  return apiGet<User[]>('/users');
}

export async function createUserApi(data: RegisterRequest): Promise<ApiResponse<User>> {
  return apiPost<User>('/users', data);
}

export async function getUserByIdApi(id: string): Promise<ApiResponse<User>> {
  return apiGet<User>(`/users/${id}`);
}

export async function updateUserApi(id: string, data: Partial<User>): Promise<ApiResponse<User>> {
  return apiPut<User>(`/users/${id}`, data);
}

export async function deleteUserApi(id: string): Promise<ApiResponse<User>> {
  return apiDelete<User>(`/users/${id}`);
}
