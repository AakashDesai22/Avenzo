/**
 * AVENZO Business Web — Role Guard Component
 * Enforces role-based access control on routes for business staff (ADMIN, BUSINESS_MANAGER, STAFF).
 * Strictly blocks CONSUMER accounts.
 */

import React from 'react';
import { Navigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { UserRoleName, getRoleDisplayLabel } from '../../types/auth';
import { ShieldAlert } from 'lucide-react';

export interface RoleGuardProps {
  allowedRoles: UserRoleName[];
  children: React.ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ allowedRoles, children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          height: '100vh',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'var(--color-background, #f8fafc)',
          color: 'var(--color-text-secondary, #64748b)',
          fontFamily: 'system-ui, -apple-system, sans-serif',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div
            style={{
              width: '2.5rem',
              height: '2.5rem',
              border: '3px solid #e2e8f0',
              borderTopColor: '#2563eb',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 1rem',
            }}
          />
          <p style={{ fontWeight: 500 }}>Verifying business credentials...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Reject CONSUMER role accounts from accessing business platform
  if (user.role?.name === 'CONSUMER') {
    return (
      <div
        style={{
          display: 'flex',
          height: '100vh',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f8fafc',
          padding: '2rem',
        }}
      >
        <div
          style={{
            maxWidth: '28rem',
            textAlign: 'center',
            backgroundColor: '#ffffff',
            padding: '2.5rem',
            borderRadius: '0.75rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e2e8f0',
          }}
        >
          <ShieldAlert size={48} color="#dc2626" style={{ margin: '0 auto 1rem' }} />
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
            Consumer Access Restricted
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748b', marginBottom: '1.5rem', lineHeight: 1.5 }}>
            Consumer accounts are not authorized to access the Avenzo Business Operations Web Platform.
            Please use the <strong>Avenzo Consumer Mobile App</strong> to manage your pantry.
          </p>
          <Link
            to="/login"
            style={{
              display: 'inline-block',
              padding: '0.625rem 1.25rem',
              backgroundColor: '#2563eb',
              color: '#ffffff',
              borderRadius: '0.375rem',
              fontWeight: 500,
              textDecoration: 'none',
              fontSize: '0.875rem',
            }}
          >
            Return to Sign In
          </Link>
        </div>
      </div>
    );
  }

  // Check role authorization for specific route
  if (user.role && !allowedRoles.includes(user.role.name)) {
    const userRoleLabel = getRoleDisplayLabel(user.role.name);
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: 'calc(100vh - 4rem)',
          padding: '2rem',
          textAlign: 'center',
        }}
      >
        <ShieldAlert size={48} color="#ef4444" style={{ marginBottom: '1rem' }} />
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.5rem' }}>
          403 — Unauthorized Access
        </h2>
        <p style={{ color: '#64748b', fontSize: '0.875rem', maxWidth: '24rem', marginBottom: '1.5rem' }}>
          Your role as <strong>{userRoleLabel}</strong> does not have permission to view this module.
        </p>
        <Link
          to="/dashboard"
          style={{
            padding: '0.5rem 1rem',
            backgroundColor: '#2563eb',
            color: '#ffffff',
            borderRadius: '0.375rem',
            fontWeight: 500,
            textDecoration: 'none',
            fontSize: '0.875rem',
          }}
        >
          Back to Operations Dashboard
        </Link>
      </div>
    );
  }

  return <>{children}</>;
};
