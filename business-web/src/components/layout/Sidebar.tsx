import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Package, Tags, Layers, Boxes, Award, TrendingUp, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, logout, hasRole } = useAuth();

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    { label: 'Products', path: '/products', icon: Package, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    { label: 'Categories', path: '/categories', icon: Tags, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    { label: 'Inventory', path: '/inventory', icon: Layers, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    { label: 'Batches', path: '/batches', icon: Boxes, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    { label: 'FEFO Pick List', path: '/fefo', icon: Award, roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'] },
    { label: 'Risk Metrics', path: '/risk', icon: TrendingUp, roles: ['ADMIN', 'BUSINESS_MANAGER'] },
  ];

  return (
    <aside
      style={{
        width: '16rem',
        backgroundColor: 'var(--color-surface)',
        borderRight: '1px solid var(--color-border)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0,
      }}
    >
      {/* Brand Header */}
      <div style={{ padding: '1.5rem 1.25rem', borderBottom: '1px solid var(--color-border)' }}>
        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--color-primary)', letterSpacing: '0.05em' }}>
          AVENZO
        </h1>
        <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem' }}>
          Business Operations
        </p>
      </div>

      {/* Navigation Links */}
      <nav style={{ flex: 1, padding: '1rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
        {navItems.map((item) => {
          if (!hasRole(item.roles as any)) return null;
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.625rem 0.875rem',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.875rem',
                fontWeight: 500,
                color: isActive ? '#ffffff' : 'var(--color-text-secondary)',
                backgroundColor: isActive ? 'var(--color-primary)' : 'transparent',
                transition: 'all 0.15s ease-in-out',
              })}
            >
              <Icon size={18} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      {/* User Footer */}
      <div
        style={{
          padding: '1rem 1.25rem',
          borderTop: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ overflow: 'hidden' }}>
          <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--color-text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {user?.first_name} {user?.last_name}
          </p>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', textTransform: 'capitalize' }}>
            {user?.role?.name}
          </span>
        </div>
        <button
          onClick={logout}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            padding: '0.375rem',
            borderRadius: 'var(--radius-sm)',
          }}
          title="Logout"
        >
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
};
