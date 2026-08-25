/**
 * AVENZO Business Web — Auth & User Types
 * Strictly aligned with FastAPI SQLAlchemy ORM Models (User, Role)
 */

export type UserRoleName = 'ADMIN' | 'BUSINESS_MANAGER' | 'STAFF' | 'CONSUMER';

export interface Role {
  id: string;
  name: UserRoleName;
  description?: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  user_type: string; // 'business' or 'consumer'
  is_active: boolean;
  role_id: string;
  role?: Role;
  last_login_at?: string;
  created_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in?: number;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  user_type?: string;
  role_id?: string;
}

/**
 * Maps backend role names to user-facing UI role labels
 */
export function getRoleDisplayLabel(roleName?: UserRoleName | string): string {
  switch (roleName) {
    case 'ADMIN':
      return 'Admin';
    case 'BUSINESS_MANAGER':
      return 'Inventory Manager';
    case 'STAFF':
      return 'Analyst';
    case 'CONSUMER':
      return 'Consumer';
    default:
      return roleName || 'Business Staff';
  }
}
