/**
 * AVENZO Business Web — Sidebar Component
 * Dynamic role-based navigation sidebar displaying UI role labels and active link highlights.
 */

import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  Tags,
  Layers,
  Boxes,
  Award,
  TrendingUp,
  BarChart3,
  Users,
  Bell,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { UserRoleName, getRoleDisplayLabel } from '../../types/auth';

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
  roles: UserRoleName[];
}

export const Sidebar: React.FC = () => {
  const { user, logout, hasRole } = useAuth();

  const navItems: NavItem[] = [
    {
      label: 'Dashboard',
      path: '/dashboard',
      icon: LayoutDashboard,
      roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'],
    },
    {
      label: 'Products',
      path: '/products',
      icon: Package,
      roles: ['ADMIN', 'BUSINESS_MANAGER'],
    },
    {
      label: 'Categories',
      path: '/categories',
      icon: Tags,
      roles: ['ADMIN', 'BUSINESS_MANAGER'],
    },
    {
      label: 'Inventory',
      path: '/inventory',
      icon: Layers,
      roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'],
    },
    {
      label: 'Batches',
      path: '/batches',
      icon: Boxes,
      roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'],
    },
    {
      label: 'FEFO Allocation',
      path: '/fefo',
      icon: Award,
      roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'],
    },
    {
      label: 'Expiry Risk',
      path: '/risk',
      icon: TrendingUp,
      roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'],
    },
    {
      label: 'Analytics',
      path: '/analytics',
      icon: BarChart3,
      roles: ['ADMIN', 'STAFF'],
    },
    {
      label: 'User Management',
      path: '/users',
      icon: Users,
      roles: ['ADMIN'],
    },
    {
      label: 'Notifications',
      path: '/notifications',
      icon: Bell,
      roles: ['ADMIN', 'BUSINESS_MANAGER', 'STAFF'],
    },
  ];

  const roleLabel = getRoleDisplayLabel(user?.role?.name);

  return (
    <aside
      style={{
        width: '16rem',
        backgroundColor: '#0f172a', // Sleek dark slate
        color: '#f8fafc',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        position: 'sticky',
        top: 0,
        boxShadow: '4px 0 10px rgba(0,0,0,0.05)',
      }}
    >
      {/* Brand Header */}
      <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <div
            style={{
              width: '2rem',
              height: '2rem',
              borderRadius: '0.375rem',
              backgroundColor: '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 800,
              fontSize: '1rem',
              color: '#ffffff',
            }}
          >
            A
          </div>
          <div>
            <h1 style={{ fontSize: '1.125rem', fontWeight: 800, letterSpacing: '0.05em', color: '#ffffff' }}>
              AVENZO
            </h1>
            <p style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Business Operations
            </p>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <nav
        style={{
          flex: 1,
          padding: '1rem 0.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.25rem',
          overflowY: 'auto',
        }}
      >
        {navItems.map((item) => {
          if (!hasRole(item.roles)) return null;
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
                borderRadius: '0.375rem',
                fontSize: '0.875rem',
                fontWeight: 500,
                color: isActive ? '#ffffff' : '#94a3b8',
                backgroundColor: isActive ? '#2563eb' : 'transparent',
                textDecoration: 'none',
                transition: 'all 0.15s ease-in-out',
              })}
            >
              <Icon size={18} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      {/* User & Role Footer */}
      <div
        style={{
          padding: '1rem 1.25rem',
          borderTop: '1px solid #1e293b',
          backgroundColor: '#020617',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ overflow: 'hidden' }}>
          <p
            style={{
              fontSize: '0.875rem',
              fontWeight: 600,
              color: '#f8fafc',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              margin: 0,
            }}
          >
            {user?.first_name} {user?.last_name}
          </p>
          <span
            style={{
              display: 'inline-block',
              fontSize: '0.7rem',
              fontWeight: 600,
              padding: '0.125rem 0.375rem',
              borderRadius: '0.25rem',
              backgroundColor: '#1e293b',
              color: '#60a5fa',
              marginTop: '0.25rem',
            }}
          >
            {roleLabel}
          </span>
        </div>
        <button
          onClick={logout}
          style={{
            background: 'none',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '0.375rem',
            borderRadius: '0.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          title="Sign out"
        >
          <LogOut size={18} />
        </button>
      </div>
    </aside>
  );
};
