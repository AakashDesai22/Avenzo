import React from 'react';

export interface HeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, action }) => {
  return (
    <header
      style={{
        padding: '1.5rem 2rem',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        backgroundColor: 'var(--color-surface)',
      }}
    >
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>{title}</h1>
        {subtitle && <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginTop: '0.25rem' }}>{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </header>
  );
};
