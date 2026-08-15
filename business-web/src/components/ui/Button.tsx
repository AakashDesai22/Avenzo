import React, { ButtonHTMLAttributes } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  className = '',
  style,
  ...props
}) => {
  const getVariantStyles = (): React.CSSProperties => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: 'var(--color-primary)',
          color: '#ffffff',
          border: 'none',
        };
      case 'secondary':
        return {
          backgroundColor: 'var(--color-surface-hover)',
          color: 'var(--color-text-primary)',
          border: '1px solid var(--color-border)',
        };
      case 'danger':
        return {
          backgroundColor: 'var(--color-danger)',
          color: '#ffffff',
          border: 'none',
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: 'var(--color-primary)',
          border: '1px solid var(--color-primary)',
        };
      case 'ghost':
        return {
          backgroundColor: 'transparent',
          color: 'var(--color-text-secondary)',
          border: 'none',
        };
    }
  };

  const getSizeStyles = (): React.CSSProperties => {
    switch (size) {
      case 'sm':
        return { padding: '0.375rem 0.75rem', fontSize: '0.875rem' };
      case 'md':
        return { padding: '0.5rem 1rem', fontSize: '1rem' };
      case 'lg':
        return { padding: '0.75rem 1.5rem', fontSize: '1.125rem' };
    }
  };

  const baseStyles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 'var(--radius-md)',
    fontWeight: 500,
    cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
    opacity: disabled || isLoading ? 0.6 : 1,
    transition: 'all 0.2s ease-in-out',
    gap: '0.5rem',
    ...getVariantStyles(),
    ...getSizeStyles(),
    ...style,
  };

  return (
    <button disabled={disabled || isLoading} style={baseStyles} className={className} {...props}>
      {isLoading && (
        <span
          style={{
            width: '1rem',
            height: '1rem',
            border: '2px solid currentColor',
            borderRightColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 0.75s linear infinite',
          }}
        />
      )}
      {children}
    </button>
  );
};
