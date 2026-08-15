import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { UserRoleName } from '../../types/auth';

export interface RoleGuardProps {
  allowedRoles: UserRoleName[];
  children: React.ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ allowedRoles, children }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', backgroundColor: 'var(--color-background)', color: 'var(--color-text-secondary)' }}>
        Loading session...
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (user.role && !allowedRoles.includes(user.role.name)) {
    return (
      <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--color-text-primary)' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--color-danger)' }}>403 — Unauthorized Access</h2>
        <p style={{ color: 'var(--color-text-secondary)', marginTop: '0.5rem' }}>
          Your account role ({user.role.name}) does not have permission to view this page.
        </p>
      </div>
    );
  }

  return <>{children}</>;
};
