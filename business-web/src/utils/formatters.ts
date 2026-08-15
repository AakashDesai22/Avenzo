/**
 * AVENZO Business Web — Utility Formatters
 * Centralized formatting helpers for Currency (INR ₹), Dates, and Expiry Badges.
 */

/**
 * Formats monetary amounts in INR (₹).
 * Centralized formatter per Phase 3 architectural requirement (Section 13).
 */
export function formatCurrency(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined) {
    return '₹0.00';
  }
  const numericVal = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(numericVal)) {
    return '₹0.00';
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  }).format(numericVal);
}

/**
 * Formats ISO date strings to human-readable format (e.g. 15 Aug 2026).
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A';
  const d = new Date(dateString);
  if (isNaN(d.getTime())) return 'N/A';
  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(d);
}

export interface ExpiryStatusBadgeProps {
  status: string;
  label: string;
  variant: 'success' | 'warning' | 'danger' | 'expired' | 'neutral';
  icon: string;
}

/**
 * Returns accessible badge properties for Expiry Status classification.
 */
export function getExpiryBadgeProps(status: string): ExpiryStatusBadgeProps {
  switch (status?.toUpperCase()) {
    case 'SAFE':
      return {
        status: 'SAFE',
        label: 'SAFE (>30 days)',
        variant: 'success',
        icon: '✓',
      };
    case 'EXPIRING_SOON':
      return {
        status: 'EXPIRING_SOON',
        label: 'EXPIRING SOON (8-30 days)',
        variant: 'warning',
        icon: '⚠',
      };
    case 'CRITICAL':
      return {
        status: 'CRITICAL',
        label: 'CRITICAL (0-7 days)',
        variant: 'danger',
        icon: '🔥',
      };
    case 'EXPIRED':
      return {
        status: 'EXPIRED',
        label: 'EXPIRED (<0 days)',
        variant: 'expired',
        icon: '⛔',
      };
    default:
      return {
        status: 'N/A',
        label: 'NON-EXPIRY',
        variant: 'neutral',
        icon: '•',
      };
  }
}
