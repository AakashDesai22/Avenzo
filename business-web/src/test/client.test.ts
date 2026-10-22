/**
 * AVENZO Business Web — API Client Unit Tests
 * Verifies API_URL normalization, token storage helpers, and endpoint URL composition.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  API_URL,
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  apiPost,
} from '../api/client';

describe('API Client Configuration and Token Storage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('constructs API_URL with valid base and api version prefix', () => {
    expect(API_URL).toMatch(/^https?:\/\/.+\/api\/v1$/);
    expect(API_URL.endsWith('/api/v1')).toBe(true);
    expect(API_URL.includes('//api')).toBe(false);
  });

  it('manages access and refresh tokens in localStorage', () => {
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();

    setTokens('mock_access_token_123', 'mock_refresh_token_456');

    expect(getAccessToken()).toBe('mock_access_token_123');
    expect(getRefreshToken()).toBe('mock_refresh_token_456');

    clearTokens();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });

  it('composes endpoint paths without duplicate versioning or double slashes', () => {
    const pantryPath = '/pantry';
    const fullEndpoint = `${API_URL}${pantryPath}`;
    expect(fullEndpoint.endsWith('/api/v1/pantry')).toBe(true);
    expect(fullEndpoint.includes('/api/v1/api/v1')).toBe(false);
  });

  it('safely extracts FastAPI detail string error message instead of generic Request failed', async () => {
    const originalFetch = globalThis.fetch;
    try {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 409,
        statusText: '',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ detail: "A product with SKU '123' already exists" }),
      } as unknown as Response);

      const res = await apiPost('/products', { sku: '123' });
      expect(res.success).toBe(false);
      expect(res.error?.message).toBe("A product with SKU '123' already exists");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  it('safely extracts FastAPI 422 list validation errors into formatted message', async () => {
    const originalFetch = globalThis.fetch;
    try {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        statusText: '',
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({
          detail: [
            { loc: ['body', 'sku'], msg: 'Field required' }
          ]
        }),
      } as unknown as Response);

      const res = await apiPost('/products', {});
      expect(res.success).toBe(false);
      expect(res.error?.message).toBe('sku: Field required');
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

