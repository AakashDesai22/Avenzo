import React, { InputHTMLAttributes } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input: React.FC<InputProps> = ({ label, error, helperText, className = '', id, style, ...props }) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', width: '100%' }}>
      {label && (
        <label htmlFor={inputId} style={{ fontSize: '0.875rem', fontWeight: 500, color: 'var(--color-text-secondary)' }}>
          {label}
        </label>
      )}
      <input
        id={inputId}
        style={{
          width: '100%',
          padding: '0.625rem 0.875rem',
          backgroundColor: 'var(--color-surface)',
          border: `1px solid ${error ? 'var(--color-danger)' : 'var(--color-border)'}`,
          borderRadius: 'var(--radius-md)',
          color: 'var(--color-text-primary)',
          outline: 'none',
          transition: 'border-color 0.2s',
          ...style,
        }}
        className={className}
        {...props}
      />
      {error && <span style={{ fontSize: '0.75rem', color: 'var(--color-danger)' }}>{error}</span>}
      {helperText && !error && <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{helperText}</span>}
    </div>
  );
};
