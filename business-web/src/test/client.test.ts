/**
 * AVENZO Business Web — API Client Unit Tests
 * Verifies API_URL normalization, token storage helpers, and endpoint URL composition.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  API_URL,
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
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
});
