/**
 * AVENZO Business Web — RBAC Unit Test Suite
 * Verifies role-based access control, navigation permissions, consumer rejection,
 * and capability checks for ADMIN, BUSINESS_MANAGER, STAFF, and CONSUMER roles.
 */

import { describe, it, expect } from 'vitest';
import { ROLE_CONFIGS, hasCapability, isRouteAllowed } from '../config/permissions.config';

describe('Avenzo RBAC & Permission Matrix Unit Tests', () => {
  describe('ADMIN Role Governance', () => {
    it('grants full administrative capabilities to ADMIN', () => {
      expect(hasCapability('ADMIN', 'view_dashboard')).toBe(true);
      expect(hasCapability('ADMIN', 'manage_products')).toBe(true);
      expect(hasCapability('ADMIN', 'manage_categories')).toBe(true);
      expect(hasCapability('ADMIN', 'adjust_inventory')).toBe(true);
      expect(hasCapability('ADMIN', 'create_batches')).toBe(true);
      expect(hasCapability('ADMIN', 'manage_users')).toBe(true);
      expect(hasCapability('ADMIN', 'view_analytics')).toBe(true);
      expect(hasCapability('ADMIN', 'view_financial_risk')).toBe(true);
    });

    it('allows ADMIN to access all business routes including /users', () => {
      expect(isRouteAllowed('ADMIN', '/dashboard')).toBe(true);
      expect(isRouteAllowed('ADMIN', '/products')).toBe(true);
      expect(isRouteAllowed('ADMIN', '/users')).toBe(true);
      expect(isRouteAllowed('ADMIN', '/analytics')).toBe(true);
    });
  });

  describe('BUSINESS_MANAGER (Inventory Manager) Role Governance', () => {
    it('grants inventory management & batch creation capabilities to BUSINESS_MANAGER', () => {
      expect(hasCapability('BUSINESS_MANAGER', 'view_dashboard')).toBe(true);
      expect(hasCapability('BUSINESS_MANAGER', 'manage_products')).toBe(true);
      expect(hasCapability('BUSINESS_MANAGER', 'manage_categories')).toBe(true);
      expect(hasCapability('BUSINESS_MANAGER', 'adjust_inventory')).toBe(true);
      expect(hasCapability('BUSINESS_MANAGER', 'create_batches')).toBe(true);
      expect(hasCapability('BUSINESS_MANAGER', 'view_financial_risk')).toBe(true);
    });

    it('denies user administration and analyst analytics to BUSINESS_MANAGER', () => {
      expect(hasCapability('BUSINESS_MANAGER', 'manage_users')).toBe(false);
      expect(hasCapability('BUSINESS_MANAGER', 'view_analytics')).toBe(false);
      expect(isRouteAllowed('BUSINESS_MANAGER', '/users')).toBe(false);
      expect(isRouteAllowed('BUSINESS_MANAGER', '/analytics')).toBe(false);
    });
  });

  describe('STAFF (Analyst) Role Governance', () => {
    it('grants read-only monitoring and analytics to STAFF', () => {
      expect(hasCapability('STAFF', 'view_dashboard')).toBe(true);
      expect(hasCapability('STAFF', 'view_products')).toBe(true);
      expect(hasCapability('STAFF', 'view_inventory')).toBe(true);
      expect(hasCapability('STAFF', 'view_batches')).toBe(true);
      expect(hasCapability('STAFF', 'view_fefo')).toBe(true);
      expect(hasCapability('STAFF', 'view_analytics')).toBe(true);
    });

    it('strictly denies mutation capabilities (products, categories, stock adjustments, batch creation) to STAFF', () => {
      expect(hasCapability('STAFF', 'manage_products')).toBe(false);
      expect(hasCapability('STAFF', 'manage_categories')).toBe(false);
      expect(hasCapability('STAFF', 'adjust_inventory')).toBe(false);
      expect(hasCapability('STAFF', 'create_batches')).toBe(false);
      expect(hasCapability('STAFF', 'manage_users')).toBe(false);
    });

    it('denies /users route to STAFF', () => {
      expect(isRouteAllowed('STAFF', '/users')).toBe(false);
    });
  });

  describe('CONSUMER Role Governance', () => {
    it('rejects CONSUMER accounts from all business routes and capabilities', () => {
      expect(ROLE_CONFIGS.CONSUMER.allowedRoutes.length).toBe(0);
      expect(ROLE_CONFIGS.CONSUMER.capabilities.length).toBe(0);
      expect(isRouteAllowed('CONSUMER', '/dashboard')).toBe(false);
      expect(isRouteAllowed('CONSUMER', '/products')).toBe(false);
      expect(isRouteAllowed('CONSUMER', '/users')).toBe(false);
    });
  });
});
