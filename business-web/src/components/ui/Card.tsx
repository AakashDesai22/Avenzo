import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({ children, title, subtitle, action, style }) => {
  return (
    <div
      style={{
        backgroundColor: 'var(--color-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--color-border)',
        padding: '1.25rem',
        boxShadow: 'var(--shadow-md)',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        ...style,
      }}
    >
      {(title || action) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            {title && <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{title}</h3>}
            {subtitle && <p style={{ fontSize: '0.875rem', color: 'var(--color-text-secondary)', marginTop: '0.125rem' }}>{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};
