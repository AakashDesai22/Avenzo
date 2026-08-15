/**
 * AVENZO Business Web — Auth API Wrapper
 */

import { apiPost, apiGet, clearTokens, setTokens, ApiResponse } from './client';
import { LoginRequest, TokenResponse, User } from '../types/auth';

export async function loginApi(credentials: LoginRequest): Promise<ApiResponse<TokenResponse>> {
  const res = await apiPost<TokenResponse>('/auth/login', credentials);
  if (res.success && res.data) {
    setTokens(res.data.access_token, res.data.refresh_token);
  }
  return res;
}

export async function getMeApi(): Promise<ApiResponse<User>> {
  return apiGet<User>('/auth/me');
}

export function logoutApi(): void {
  clearTokens();
}
