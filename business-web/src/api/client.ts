/**
 * AVENZO Business Web — API Client
 * Central HTTP client for all API communication.
 * All network calls MUST use functions from this module.
 * No direct fetch/axios calls allowed in components.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = import.meta.env.VITE_API_VERSION || '/api/v1';

export const API_URL = `${API_BASE_URL}${API_VERSION}`;

/**
 * Get the stored JWT access token from localStorage.
 */
function getAccessToken(): string | null {
  return localStorage.getItem('avenzo_access_token');
}

/**
 * Base headers for all API requests.
 */
function getHeaders(withAuth = true): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  if (withAuth) {
    const token = getAccessToken();
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * Standard API response wrapper.
 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
  error?: {
    code: string;
    message: string;
    details?: unknown;
  };
  meta?: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

/**
 * Core fetch wrapper with error handling.
 */
async function request<T>(
  path: string,
  options: RequestInit = {},
  withAuth = true,
): Promise<ApiResponse<T>> {
  const url = `${API_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getHeaders(withAuth),
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    return {
      success: false,
      error: errorBody.error || {
        code: `HTTP_${response.status}`,
        message: response.statusText,
      },
    };
  }

  if (response.status === 204) {
    return { success: true };
  }

  const body = await response.json();
  return body;
}

/**
 * GET request
 */
export function apiGet<T>(
  path: string,
  params?: Record<string, string | number | boolean>,
): Promise<ApiResponse<T>> {
  const queryString = params
    ? '?' + new URLSearchParams(params as Record<string, string>).toString()
    : '';
  return request<T>(`${path}${queryString}`, { method: 'GET' });
}

/**
 * POST request
 */
export function apiPost<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
  return request<T>(path, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * PUT request
 */
export function apiPut<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
  return request<T>(path, {
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * PATCH request
 */
export function apiPatch<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
  return request<T>(path, {
    method: 'PATCH',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * DELETE request
 */
export function apiDelete<T>(path: string): Promise<ApiResponse<T>> {
  return request<T>(path, { method: 'DELETE' });
}
