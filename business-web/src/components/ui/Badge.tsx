import React from 'react';
import { getExpiryBadgeProps } from '../../utils/formatters';

export interface BadgeProps {
  status?: string;
  variant?: 'success' | 'warning' | 'danger' | 'expired' | 'neutral' | 'info';
  children?: React.ReactNode;
  icon?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, variant, children, icon }) => {
  if (status) {
    const props = getExpiryBadgeProps(status);
    variant = props.variant;
    children = children || props.label;
    icon = icon || props.icon;
  }

  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'success':
        return { backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success)', border: '1px solid rgba(16, 185, 129, 0.3)' };
      case 'warning':
        return { backgroundColor: 'var(--color-warning-bg)', color: 'var(--color-warning)', border: '1px solid rgba(245, 158, 11, 0.3)' };
      case 'danger':
        return { backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger)', border: '1px solid rgba(239, 68, 68, 0.3)' };
      case 'expired':
        return { backgroundColor: 'var(--color-expired-bg)', color: '#fca5a5', border: '1px solid rgba(153, 27, 27, 0.5)' };
      case 'info':
        return { backgroundColor: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' };
      case 'neutral':
      default:
        return { backgroundColor: 'var(--color-neutral-bg)', color: 'var(--color-neutral)', border: '1px solid rgba(100, 116, 139, 0.3)' };
    }
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.375rem',
        padding: '0.25rem 0.625rem',
        borderRadius: 'var(--radius-full)',
        fontSize: '0.75rem',
        fontWeight: 600,
        whiteSpace: 'nowrap',
        ...getVariantStyles(),
      }}
    >
      {icon && <span>{icon}</span>}
      {children}
    </span>
  );
};
