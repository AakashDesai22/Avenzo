/**
 * AVENZO Business Web — Centralized Role & Permission Configuration
 * Authoritative source of truth for frontend RBAC capabilities, route guards,
 * and navigation accessibility aligned with FastAPI backend `require_roles()`.
 */

import { UserRoleName } from '../types/auth';

export type Capability =
  | 'view_dashboard'
  | 'view_products'
  | 'manage_products'
  | 'manage_categories'
  | 'view_inventory'
  | 'adjust_inventory'
  | 'view_batches'
  | 'create_batches'
  | 'view_fefo'
  | 'view_expiry_risk'
  | 'view_financial_risk'
  | 'view_analytics'
  | 'manage_users'
  | 'view_notifications'
  | 'view_orders'
  | 'manage_fulfillment';

export interface RoleConfig {
  roleName: UserRoleName;
  displayLabel: string;
  description: string;
  allowedRoutes: string[];
  capabilities: Capability[];
}

/**
 * Centralized Role Configuration Matrix
 */
export const ROLE_CONFIGS: Record<UserRoleName, RoleConfig> = {
  ADMIN: {
    roleName: 'ADMIN',
    displayLabel: 'Admin',
    description: 'Full administrative access, user management, and system governance.',
    allowedRoutes: [
      '/dashboard',
      '/orders',
      '/products',
      '/categories',
      '/inventory',
      '/batches',
      '/warehouses',
      '/fefo',
      '/risk',
      '/analytics',
      '/users',
      '/notifications',
    ],
    capabilities: [
      'view_dashboard',
      'view_orders',
      'manage_fulfillment',
      'view_products',
      'manage_products',
      'manage_categories',
      'view_inventory',
      'adjust_inventory',
      'view_batches',
      'create_batches',
      'view_fefo',
      'view_expiry_risk',
      'view_financial_risk',
      'view_analytics',
      'manage_users',
      'view_notifications',
    ],
  },
  BUSINESS_MANAGER: {
    roleName: 'BUSINESS_MANAGER',
    displayLabel: 'Inventory Manager',
    description: 'Receiving oversight, batch recording, inventory adjustments, and risk management.',
    allowedRoutes: [
      '/dashboard',
      '/orders',
      '/products',
      '/categories',
      '/inventory',
      '/batches',
      '/warehouses',
      '/fefo',
      '/risk',
      '/notifications',
    ],
    capabilities: [
      'view_dashboard',
      'view_orders',
      'manage_fulfillment',
      'view_products',
      'manage_products',
      'manage_categories',
      'view_inventory',
      'adjust_inventory',
      'view_batches',
      'create_batches',
      'view_fefo',
      'view_expiry_risk',
      'view_financial_risk',
      'view_notifications',
    ],
  },
  STAFF: {
    roleName: 'STAFF',
    displayLabel: 'Analyst',
    description: 'Read-only operational monitoring, FEFO analysis, and waste metrics forecasting.',
    allowedRoutes: [
      '/dashboard',
      '/orders',
      '/inventory',
      '/batches',
      '/warehouses',
      '/fefo',
      '/risk',
      '/analytics',
      '/notifications',
    ],
    capabilities: [
      'view_dashboard',
      'view_orders',
      'view_products',
      'view_inventory',
      'view_batches',
      'view_fefo',
      'view_expiry_risk',
      'view_analytics',
      'view_notifications',
    ],
  },
  CONSUMER: {
    roleName: 'CONSUMER',
    displayLabel: 'Consumer',
    description: 'B2C mobile pantry user. Access to business web platform is prohibited.',
    allowedRoutes: [],
    capabilities: [],
  },
};

/**
 * Checks if a specific role possesses a required capability.
 */
export function hasCapability(roleName: UserRoleName | undefined, capability: Capability): boolean {
  if (!roleName || !ROLE_CONFIGS[roleName]) return false;
  return ROLE_CONFIGS[roleName].capabilities.includes(capability);
}

/**
 * Checks if a specific role is authorized to access a target path.
 */
export function isRouteAllowed(roleName: UserRoleName | undefined, path: string): boolean {
  if (!roleName || !ROLE_CONFIGS[roleName]) return false;
  const config = ROLE_CONFIGS[roleName];
  return config.allowedRoutes.some((route) => path === route || path.startsWith(`${route}/`));
}
