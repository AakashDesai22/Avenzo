/**
 * AVENZO Business Web — API Client
 * Centralized fetch client with automatic JWT authorization header injection,
 * single-retry token refresh logic on 401 response, and strict type safety.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = import.meta.env.VITE_API_VERSION || '/api/v1';

export const API_URL = `${API_BASE_URL}${API_VERSION}`;

/**
 * Get stored tokens from localStorage.
 */
export function getAccessToken(): string | null {
  return localStorage.getItem('avenzo_access_token');
}

export function getRefreshToken(): string | null {
  return localStorage.getItem('avenzo_refresh_token');
}

export function setTokens(access_token: string, refresh_token: string): void {
  localStorage.setItem('avenzo_access_token', access_token);
  localStorage.setItem('avenzo_refresh_token', refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem('avenzo_access_token');
  localStorage.removeItem('avenzo_refresh_token');
}

/**
 * Base headers for API requests.
 */
function getHeaders(withAuth = true): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  if (withAuth) {
    const token = getAccessToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * Standard backend ApiResponse wrapper.
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

let isRefreshing = false;

/**
 * Attempts to refresh the JWT access token once.
 */
async function refreshAccessToken(): Promise<boolean> {
  const refresh_token = getRefreshToken();
  if (!refresh_token) {
    clearTokens();
    return false;
  }

  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token }),
    });

    if (!response.ok) {
      clearTokens();
      return false;
    }

    const body = await response.json();
    if (body.success && body.data?.access_token) {
      setTokens(body.data.access_token, body.data.refresh_token || refresh_token);
      return true;
    }

    clearTokens();
    return false;
  } catch {
    clearTokens();
    return false;
  }
}

/**
 * Core fetch wrapper with 401 token refresh interceptor.
 */
async function request<T>(
  path: string,
  options: RequestInit = {},
  withAuth = true,
  isRetry = false,
): Promise<ApiResponse<T>> {
  const url = `${API_URL}${path}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      ...getHeaders(withAuth),
      ...(options.headers || {}),
    },
  });

  // Handle 401 Unauthorized
  if (response.status === 401 && withAuth && !isRetry) {
    const isAuthEndpoint = path.includes('/auth/login') || path.includes('/auth/refresh');
    if (!isAuthEndpoint) {
      if (!isRefreshing) {
        isRefreshing = true;
        const refreshed = await refreshAccessToken();
        isRefreshing = false;

        if (refreshed) {
          // Retry original request once with new token
          return request<T>(path, options, withAuth, true);
        }
      }

      // Refresh failed -> clear auth & redirect
      clearTokens();
      if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
        window.location.href = '/login?session_expired=true';
      }
    }
  }

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    return {
      success: false,
      error: errorBody.error || {
        code: `HTTP_${response.status}`,
        message: response.statusText || 'Request failed',
      },
    };
  }

  if (response.status === 204) {
    return { success: true };
  }

  const body = await response.json();
  return body;
}

export function apiGet<T>(
  path: string,
  params?: Record<string, string | number | boolean | undefined>,
): Promise<ApiResponse<T>> {
  const cleanParams: Record<string, string> = {};
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) {
        cleanParams[k] = String(v);
      }
    });
  }
  const queryString = Object.keys(cleanParams).length > 0 ? '?' + new URLSearchParams(cleanParams).toString() : '';
  return request<T>(`${path}${queryString}`, { method: 'GET' });
}

export function apiPost<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
  return request<T>(path, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiPut<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
  return request<T>(path, {
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function apiDelete<T>(path: string): Promise<ApiResponse<T>> {
  return request<T>(path, { method: 'DELETE' });
}
