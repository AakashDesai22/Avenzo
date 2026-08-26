/**
 * AVENZO Business Web — Order Detail Modal Component
 * Displays comprehensive order information, line items, lazy-loaded FEFO batch pick lists,
 * and operational fulfillment action buttons.
 */

import React, { useEffect, useState } from 'react';
import { X, CheckCircle, Package, Truck, ShoppingBag, AlertTriangle, Clock, MapPin, CreditCard } from 'lucide-react';
import { Order, OrderBatchAllocation, OrderStatus } from '../../types/orders';
import { getOrderAllocations, confirmOrder, allocateOrderFefo, packOrder, dispatchOrder, deliverOrder, cancelOrder } from '../../api/orders.api';
import { useAuth } from '../../context/AuthContext';

interface OrderDetailModalProps {
  order: Order | null;
  onClose: () => void;
  onOrderUpdated: () => void;
}

export const OrderDetailModal: React.FC<OrderDetailModalProps> = ({ order, onClose, onOrderUpdated }) => {
  const { hasRole, can } = useAuth();
  const canManage = can('manage_fulfillment') || hasRole(['ADMIN', 'BUSINESS_MANAGER']);

  const [allocations, setAllocations] = useState<OrderBatchAllocation[]>([]);
  const [isAllocLoading, setIsAllocLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!order) return;
    setIsAllocLoading(true);
    setErrorMsg(null);
    getOrderAllocations(order.id)
      .then((res) => {
        if (res.success && res.data) {
          setAllocations(res.data);
        } else {
          setAllocations([]);
        }
      })
      .catch(() => setAllocations([]))
      .finally(() => setIsAllocLoading(false));
  }, [order]);

  if (!order) return null;

  const getStatusBadgeStyle = (status: OrderStatus) => {
    switch (status) {
      case 'PENDING':
        return { bg: '#fef3c7', text: '#d97706', border: '#fcd34d' };
      case 'CONFIRMED':
        return { bg: '#dbeafe', text: '#2563eb', border: '#93c5fd' };
      case 'ALLOCATED':
        return { bg: '#e0e7ff', text: '#4f46e5', border: '#a5b4fc' };
      case 'PACKED':
        return { bg: '#f3e8ff', text: '#9333ea', border: '#d8b4fe' };
      case 'SHIPPED':
        return { bg: '#cff4fc', text: '#0891b2', border: '#a5f3fc' };
      case 'DELIVERED':
        return { bg: '#dcfce7', text: '#16a34a', border: '#86efac' };
      case 'CANCELLED':
      case 'FAILED':
        return { bg: '#fee2e2', text: '#dc2626', border: '#fca5a5' };
      default:
        return { bg: '#f1f5f9', text: '#64748b', border: '#cbd5e1' };
    }
  };

  const badgeStyle = getStatusBadgeStyle(order.status);

  const handleAction = async (actionType: string, actionFn: () => Promise<unknown>) => {
    if (actionType === 'CANCEL' && !window.confirm('Are you sure you want to cancel this order and release stock reservations?')) {
      return;
    }
    setActionLoading(actionType);
    setErrorMsg(null);
    try {
      const res = (await actionFn()) as { success: boolean; error?: { message: string }; message?: string };
      if (res.success) {
        onOrderUpdated();
        // Refresh allocations
        const allocRes = await getOrderAllocations(order.id);
        if (allocRes.success && allocRes.data) {
          setAllocations(allocRes.data);
        }
      } else {
        setErrorMsg(res.error?.message || 'Operation failed.');
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || 'Operation failed due to a network error.');
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '1rem',
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#0f172a',
          color: '#f8fafc',
          borderRadius: '0.75rem',
          width: '100%',
          maxWidth: '56rem',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          border: '1px solid #1e293b',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid #1e293b',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#020617',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <ShoppingBag size={24} color="#3b82f6" />
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>
                  Order {order.order_number}
                </h2>
                <span
                  style={{
                    padding: '0.2rem 0.6rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    backgroundColor: badgeStyle.bg,
                    color: badgeStyle.text,
                    border: `1px solid ${badgeStyle.border}`,
                  }}
                >
                  {order.status}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.25rem 0 0 0' }}>
                Placed on {new Date(order.created_at).toLocaleString()} • Customer ID: {order.user_id.slice(0, 8)}...
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '0.375rem',
              borderRadius: '0.375rem',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {errorMsg && (
            <div
              style={{
                padding: '0.875rem 1rem',
                borderRadius: '0.375rem',
                backgroundColor: 'rgba(220, 38, 38, 0.1)',
                border: '1px solid #ef4444',
                color: '#f87171',
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              <AlertTriangle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Shipping & Financial Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
            {/* Address Panel */}
            <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#60a5fa', marginBottom: '0.5rem' }}>
                <MapPin size={16} />
                <h4 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 600 }}>Delivery Address</h4>
              </div>
              <p style={{ margin: 0, fontSize: '0.875rem', color: '#cbd5e1', lineHeight: '1.4' }}>
                {order.shipping_address}
              </p>
              {order.notes && (
                <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.75rem', color: '#94a3b8', fontStyle: 'italic' }}>
                  Note: {order.notes}
                </p>
              )}
            </div>

            {/* Payment Panel */}
            <div style={{ backgroundColor: '#1e293b', padding: '1rem', borderRadius: '0.5rem', border: '1px solid #334155' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#60a5fa', marginBottom: '0.5rem' }}>
                <CreditCard size={16} />
                <h4 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 600 }}>Payment & Billing</h4>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem', color: '#cbd5e1' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Method:</span>
                  <span style={{ fontWeight: 600, color: '#f8fafc' }}>{order.payment_method}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Payment Status:</span>
                  <span style={{ fontWeight: 600, color: order.payment_status === 'PAID' ? '#4ade80' : '#f87171' }}>
                    {order.payment_status}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #334155', paddingTop: '0.25rem', marginTop: '0.25rem' }}>
                  <span>Total Amount:</span>
                  <span style={{ fontWeight: 700, color: '#60a5fa' }}>${Number(order.total_amount).toFixed(2)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Line Items Table */}
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem', color: '#f8fafc' }}>
              Order Line Items
            </h3>
            <div style={{ overflowX: 'auto', border: '1px solid #334155', borderRadius: '0.5rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ backgroundColor: '#020617', borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                    <th style={{ padding: '0.75rem 1rem' }}>Product</th>
                    <th style={{ padding: '0.75rem 1rem' }}>SKU</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Unit Price</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Qty</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Total</th>
                    <th style={{ padding: '0.75rem 1rem' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {order.items.map((item) => (
                    <tr key={item.id} style={{ borderBottom: '1px solid #1e293b' }}>
                      <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#f8fafc' }}>
                        {item.product?.name || 'Product'}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#94a3b8' }}>
                        {item.product?.sku || '-'}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: '#cbd5e1' }}>
                        ${Number(item.unit_price).toFixed(2)}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#f8fafc' }}>
                        {item.quantity}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: '#60a5fa' }}>
                        ${Number(item.total_price).toFixed(2)}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span
                          style={{
                            padding: '0.125rem 0.5rem',
                            borderRadius: '0.25rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            backgroundColor: item.fulfillment_status === 'SHIPPED' || item.fulfillment_status === 'DELIVERED' ? 'rgba(34,197,94,0.15)' : 'rgba(148,163,184,0.15)',
                            color: item.fulfillment_status === 'SHIPPED' || item.fulfillment_status === 'DELIVERED' ? '#4ade80' : '#94a3b8',
                          }}
                        >
                          {item.fulfillment_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* FEFO Pick List / Batch Allocation Panel */}
          <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '0.5rem', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Package size={18} color="#a855f7" />
                <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0, color: '#f8fafc' }}>
                  FEFO Batch Allocation Pick List
                </h3>
              </div>
              {isAllocLoading && (
                <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Clock size={12} /> Loading allocations...
                </span>
              )}
            </div>

            {allocations.length === 0 ? (
              <p style={{ margin: 0, fontSize: '0.875rem', color: '#94a3b8', fontStyle: 'italic' }}>
                {order.status === 'PENDING' || order.status === 'CONFIRMED'
                  ? 'FEFO batch allocation has not been executed yet for this order.'
                  : 'No batch allocation records found.'}
              </p>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.8rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Batch Number</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Expiry Date</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Allocated Qty</th>
                      <th style={{ padding: '0.5rem 0.75rem' }}>Inventory ID</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allocations.map((alloc) => (
                      <tr key={alloc.id} style={{ borderBottom: '1px solid #0f172a' }}>
                        <td style={{ padding: '0.5rem 0.75rem', fontWeight: 700, color: '#c084fc' }}>
                          {alloc.batch_number || alloc.batch_id.slice(0, 8)}
                        </td>
                        <td style={{ padding: '0.5rem 0.75rem', color: '#f8fafc' }}>
                          {alloc.expiry_date || 'N/A'}
                        </td>
                        <td style={{ padding: '0.5rem 0.75rem', fontWeight: 700, color: '#60a5fa' }}>
                          {alloc.allocated_quantity} units
                        </td>
                        <td style={{ padding: '0.5rem 0.75rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                          {alloc.inventory_id.slice(0, 12)}...
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Operational Fulfillment Actions Footer */}
        {canManage && order.status !== 'DELIVERED' && order.status !== 'CANCELLED' && order.status !== 'FAILED' && (
          <div
            style={{
              padding: '1rem 1.5rem',
              borderTop: '1px solid #1e293b',
              backgroundColor: '#020617',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '1rem',
              flexWrap: 'wrap',
            }}
          >
            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              Operational Actions:
            </span>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              {/* Pre-shipment Cancel */}
              {['PENDING', 'CONFIRMED', 'ALLOCATED', 'PACKED'].includes(order.status) && (
                <button
                  onClick={() => handleAction('CANCEL', () => cancelOrder(order.id))}
                  disabled={actionLoading !== null}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    backgroundColor: 'rgba(220, 38, 38, 0.15)',
                    color: '#f87171',
                    border: '1px solid #ef4444',
                    cursor: actionLoading !== null ? 'not-allowed' : 'pointer',
                    opacity: actionLoading !== null ? 0.6 : 1,
                  }}
                >
                  {actionLoading === 'CANCEL' ? 'Cancelling...' : 'Cancel Order'}
                </button>
              )}

              {/* Status Specific Operations */}
              {order.status === 'PENDING' && (
                <button
                  onClick={() => handleAction('CONFIRM', () => confirmOrder(order.id))}
                  disabled={actionLoading !== null}
                  style={{
                    padding: '0.5rem 1.25rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    backgroundColor: '#2563eb',
                    color: '#ffffff',
                    border: 'none',
                    cursor: actionLoading !== null ? 'not-allowed' : 'pointer',
                    opacity: actionLoading !== null ? 0.6 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <CheckCircle size={16} />
                  {actionLoading === 'CONFIRM' ? 'Confirming...' : 'Confirm Order'}
                </button>
              )}

              {order.status === 'CONFIRMED' && (
                <button
                  onClick={() => handleAction('ALLOCATE', () => allocateOrderFefo(order.id))}
                  disabled={actionLoading !== null}
                  style={{
                    padding: '0.5rem 1.25rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    backgroundColor: '#4f46e5',
                    color: '#ffffff',
                    border: 'none',
                    cursor: actionLoading !== null ? 'not-allowed' : 'pointer',
                    opacity: actionLoading !== null ? 0.6 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <Package size={16} />
                  {actionLoading === 'ALLOCATE' ? 'Allocating FEFO...' : 'Allocate FEFO Batches'}
                </button>
              )}

              {order.status === 'ALLOCATED' && (
                <button
                  onClick={() => handleAction('PACK', () => packOrder(order.id))}
                  disabled={actionLoading !== null}
                  style={{
                    padding: '0.5rem 1.25rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    backgroundColor: '#9333ea',
                    color: '#ffffff',
                    border: 'none',
                    cursor: actionLoading !== null ? 'not-allowed' : 'pointer',
                    opacity: actionLoading !== null ? 0.6 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <Package size={16} />
                  {actionLoading === 'PACK' ? 'Packing...' : 'Pack Order'}
                </button>
              )}

              {order.status === 'PACKED' && (
                <button
                  onClick={() => handleAction('DISPATCH', () => dispatchOrder(order.id))}
                  disabled={actionLoading !== null}
                  style={{
                    padding: '0.5rem 1.25rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    backgroundColor: '#0891b2',
                    color: '#ffffff',
                    border: 'none',
                    cursor: actionLoading !== null ? 'not-allowed' : 'pointer',
                    opacity: actionLoading !== null ? 0.6 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <Truck size={16} />
                  {actionLoading === 'DISPATCH' ? 'Dispatching...' : 'Dispatch & Ship'}
                </button>
              )}

              {order.status === 'SHIPPED' && (
                <button
                  onClick={() => handleAction('DELIVER', () => deliverOrder(order.id))}
                  disabled={actionLoading !== null}
                  style={{
                    padding: '0.5rem 1.25rem',
                    borderRadius: '0.375rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    backgroundColor: '#16a34a',
                    color: '#ffffff',
                    border: 'none',
                    cursor: actionLoading !== null ? 'not-allowed' : 'pointer',
                    opacity: actionLoading !== null ? 0.6 : 1,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  <CheckCircle size={16} />
                  {actionLoading === 'DELIVER' ? 'Delivering...' : 'Mark Delivered'}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
