/**
 * AVENZO Business Web — Auth API
 * Authentication-related API calls.
 * Phase 1+ implementation.
 */

import { apiPost } from './client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    role: string;
  };
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

/**
 * Login with email and password.
 * Stores tokens in localStorage after successful login.
 */
export async function login(credentials: LoginRequest) {
  const response = await apiPost<LoginResponse>('/auth/login', credentials);

  if (response.success && response.data) {
    localStorage.setItem('avenzo_access_token', response.data.access_token);
    localStorage.setItem('avenzo_refresh_token', response.data.refresh_token);
  }

  return response;
}

/**
 * Logout — removes stored tokens.
 */
export function logout() {
  localStorage.removeItem('avenzo_access_token');
  localStorage.removeItem('avenzo_refresh_token');
}

/**
 * Refresh the access token.
 */
export function refreshAccessToken(refreshToken: string) {
  return apiPost<{ access_token: string }>('/auth/refresh', {
    refresh_token: refreshToken,
  });
}
