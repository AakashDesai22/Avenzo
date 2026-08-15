import React from 'react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T) => React.ReactNode;
  width?: string;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  isLoading?: boolean;
  emptyMessage?: string;
}

export function Table<T>({ columns, data, keyExtractor, isLoading, emptyMessage = 'No records found.' }: TableProps<T>) {
  return (
    <div
      style={{
        width: '100%',
        overflowX: 'auto',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        backgroundColor: 'var(--color-surface)',
      }}
    >
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
        <thead>
          <tr style={{ backgroundColor: 'var(--color-border-subtle)', borderBottom: '1px solid var(--color-border)' }}>
            {columns.map((col) => (
              <th
                key={col.key}
                style={{
                  padding: '0.75rem 1rem',
                  fontWeight: 600,
                  color: 'var(--color-text-secondary)',
                  width: col.width,
                }}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
                Loading data...
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-muted)' }}>
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr
                key={keyExtractor(item)}
                style={{
                  borderBottom: '1px solid var(--color-border)',
                  transition: 'background-color 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--color-surface-hover)')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
              >
                {columns.map((col) => (
                  <td key={col.key} style={{ padding: '0.75rem 1rem', color: 'var(--color-text-primary)' }}>
                    {col.render ? col.render(item) : String((item as Record<string, unknown>)[col.key] ?? '')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
