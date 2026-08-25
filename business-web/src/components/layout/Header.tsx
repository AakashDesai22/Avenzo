/**
 * AVENZO Business Web — Header Component
 * Top bar displaying current area context, business role badge, and system notifications trigger.
 */

import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { getRoleDisplayLabel } from '../../types/auth';
import { Bell, UserCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

export interface HeaderProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, action }) => {
  const { user } = useAuth();
  const roleLabel = getRoleDisplayLabel(user?.role?.name);

  return (
    <header
      style={{
        height: '4rem',
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 2rem',
        position: 'sticky',
        top: 0,
        zIndex: 10,
      }}
    >
      <div>
        <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
          {title || 'Business Operations Platform'}
        </h2>
        <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>
          {subtitle || 'Real-time FEFO Inventory & Expiry Intelligence'}
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        {action}
        <Link
          to="/notifications"
          style={{
            position: 'relative',
            color: '#64748b',
            padding: '0.5rem',
            borderRadius: '0.375rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            textDecoration: 'none',
          }}
          title="Notifications"
        >
          <Bell size={20} />
        </Link>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            paddingLeft: '1rem',
            borderLeft: '1px solid #e2e8f0',
          }}
        >
          <div
            style={{
              width: '2.25rem',
              height: '2.25rem',
              borderRadius: '50%',
              backgroundColor: '#eff6ff',
              color: '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.875rem',
            }}
          >
            {user?.first_name?.[0] || 'U'}
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#0f172a', margin: 0 }}>
              {user?.first_name} {user?.last_name}
            </p>
            <span
              style={{
                fontSize: '0.75rem',
                color: '#2563eb',
                fontWeight: 600,
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.25rem',
              }}
            >
              <UserCheck size={12} />
              {roleLabel}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
