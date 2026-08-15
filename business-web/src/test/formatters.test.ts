import { formatCurrency, formatDate, getExpiryBadgeProps } from '../utils/formatters';

describe('Formatters Utility', () => {
  it('formats currency in INR (₹)', () => {
    expect(formatCurrency(1000)).toContain('1,000.00');
    expect(formatCurrency('250.50')).toContain('250.50');
    expect(formatCurrency(null)).toContain('0.00');
  });

  it('formats date string cleanly', () => {
    expect(formatDate('2026-08-20')).toContain('2026');
    expect(formatDate(null)).toBe('N/A');
  });

  it('returns appropriate accessible props for expiry status', () => {
    expect(getExpiryBadgeProps('SAFE').variant).toBe('success');
    expect(getExpiryBadgeProps('EXPIRING_SOON').variant).toBe('warning');
    expect(getExpiryBadgeProps('CRITICAL').variant).toBe('danger');
    expect(getExpiryBadgeProps('EXPIRED').variant).toBe('expired');
    expect(getExpiryBadgeProps('N/A').variant).toBe('neutral');
  });
});
