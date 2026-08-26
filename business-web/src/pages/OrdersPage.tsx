/**
 * AVENZO Business Web — Order Fulfillment Workspace Page (/orders)
 * Command center for business roles (ADMIN, BUSINESS_MANAGER, STAFF) to view
 * consumer order queues, metrics, status filters, and execute fulfillment transitions.
 */

import React, { useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ShoppingBag,
  RefreshCw,
  Search,
  Filter,
  CheckCircle,
  Package,
  Truck,
  AlertCircle,
  Eye,
} from 'lucide-react';
import { listOrders, confirmOrder, allocateOrderFefo, packOrder, dispatchOrder, deliverOrder } from '../api/orders.api';
import { Order, OrderStatus } from '../types/orders';
import { OrderDetailModal } from '../components/orders/OrderDetailModal';
import { useAuth } from '../context/AuthContext';

export const OrdersPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { hasRole, can } = useAuth();
  const canManage = can('manage_fulfillment') || hasRole(['ADMIN', 'BUSINESS_MANAGER']);

  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Query order list with status filter
  const { data: response, isLoading, isError, refetch } = useQuery({
    queryKey: ['orders', statusFilter],
    queryFn: () => listOrders(statusFilter === 'ALL' ? undefined : statusFilter),
  });

  const orders: Order[] = response?.data || [];

  // Calculate live metric counts from real database records
  const counts = {
    total: orders.length,
    pending: orders.filter((o) => o.status === 'PENDING').length,
    confirmed: orders.filter((o) => o.status === 'CONFIRMED').length,
    allocated: orders.filter((o) => o.status === 'ALLOCATED').length,
    packed: orders.filter((o) => o.status === 'PACKED').length,
    shipped: orders.filter((o) => o.status === 'SHIPPED').length,
    delivered: orders.filter((o) => o.status === 'DELIVERED').length,
    cancelled: orders.filter((o) => o.status === 'CANCELLED' || o.status === 'FAILED').length,
  };

  // Filter orders by search term
  const filteredOrders = orders.filter((o) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      o.order_number.toLowerCase().includes(term) ||
      o.user_id.toLowerCase().includes(term) ||
      o.shipping_address.toLowerCase().includes(term)
    );
  });

  const handleAction = async (orderId: string, actionType: string, actionFn: () => Promise<unknown>) => {
    if (actionType === 'CANCEL' && !window.confirm('Are you sure you want to cancel this order?')) {
      return;
    }
    setActionLoadingId(`${orderId}-${actionType}`);
    setErrorMsg(null);
    try {
      const res = (await actionFn()) as { success: boolean; data?: Order; error?: { message: string }; message?: string };
      if (res.success) {
        await queryClient.invalidateQueries({ queryKey: ['orders'] });
        if (selectedOrder && selectedOrder.id === orderId && res.data) {
          setSelectedOrder(res.data);
        }
      } else {
        setErrorMsg(res.error?.message || 'Operation failed.');
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setErrorMsg(e.message || 'Operation failed due to a network error.');
    } finally {
      setActionLoadingId(null);
    }
  };

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
            <ShoppingBag size={28} color="#2563eb" />
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#f8fafc', margin: 0, letterSpacing: '-0.025em' }}>
              Order Fulfillment Workspace
            </h1>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#94a3b8', margin: '0.25rem 0 0 0' }}>
            Process consumer purchase orders through server-side FEFO allocation and fulfillment stages.
          </p>
        </div>

        <button
          onClick={() => refetch()}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            borderRadius: '0.375rem',
            backgroundColor: '#1e293b',
            color: '#f8fafc',
            border: '1px solid #334155',
            cursor: 'pointer',
            fontSize: '0.875rem',
            fontWeight: 600,
          }}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Live Summary Metric Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '0.75rem',
        }}
      >
        {[
          { label: 'Pending', count: counts.pending, color: '#d97706', bg: 'rgba(217, 119, 6, 0.1)' },
          { label: 'Confirmed', count: counts.confirmed, color: '#2563eb', bg: 'rgba(37, 99, 235, 0.1)' },
          { label: 'Allocated', count: counts.allocated, color: '#4f46e5', bg: 'rgba(79, 70, 229, 0.1)' },
          { label: 'Packed', count: counts.packed, color: '#9333ea', bg: 'rgba(147, 51, 234, 0.1)' },
          { label: 'Shipped', count: counts.shipped, color: '#0891b2', bg: 'rgba(8, 145, 178, 0.1)' },
          { label: 'Delivered', count: counts.delivered, color: '#16a34a', bg: 'rgba(22, 163, 74, 0.1)' },
          { label: 'Cancelled', count: counts.cancelled, color: '#dc2626', bg: 'rgba(220, 38, 38, 0.1)' },
        ].map((card) => (
          <div
            key={card.label}
            style={{
              backgroundColor: '#0f172a',
              padding: '0.875rem 1rem',
              borderRadius: '0.5rem',
              border: '1px solid #1e293b',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.25rem',
            }}
          >
            <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>{card.label}</span>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: card.color }}>{card.count}</span>
          </div>
        ))}
      </div>

      {/* Filter and Search Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          flexWrap: 'wrap',
          backgroundColor: '#0f172a',
          padding: '1rem',
          borderRadius: '0.5rem',
          border: '1px solid #1e293b',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1, minWidth: '240px' }}>
          <Search size={18} color="#94a3b8" />
          <input
            type="text"
            placeholder="Search order number or customer ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '0.375rem',
              padding: '0.5rem 0.75rem',
              color: '#f8fafc',
              fontSize: '0.875rem',
              outline: 'none',
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Filter size={18} color="#94a3b8" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              backgroundColor: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '0.375rem',
              padding: '0.5rem 0.75rem',
              color: '#f8fafc',
              fontSize: '0.875rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="ALLOCATED">Allocated</option>
            <option value="PACKED">Packed</option>
            <option value="SHIPPED">Shipped</option>
            <option value="DELIVERED">Delivered</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </div>
      </div>

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
          <AlertCircle size={18} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Main Order Queue View */}
      {isLoading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
          <RefreshCw size={24} style={{ animation: 'spin 1s linear infinite' }} />
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>Loading operational order queue...</p>
        </div>
      ) : isError ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#f87171' }}>
          <AlertCircle size={24} />
          <p style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>Failed to load order queue from backend.</p>
        </div>
      ) : filteredOrders.length === 0 ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8', backgroundColor: '#0f172a', borderRadius: '0.5rem', border: '1px solid #1e293b' }}>
          <ShoppingBag size={32} color="#64748b" />
          <p style={{ marginTop: '0.5rem', fontSize: '1rem', fontWeight: 600 }}>No orders found</p>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>No orders match the current status filter or search criteria.</p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto', backgroundColor: '#0f172a', borderRadius: '0.5rem', border: '1px solid #1e293b' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ backgroundColor: '#020617', borderBottom: '1px solid #1e293b', color: '#94a3b8' }}>
                <th style={{ padding: '0.875rem 1rem' }}>Order #</th>
                <th style={{ padding: '0.875rem 1rem' }}>Customer ID</th>
                <th style={{ padding: '0.875rem 1rem' }}>Date</th>
                <th style={{ padding: '0.875rem 1rem' }}>Total</th>
                <th style={{ padding: '0.875rem 1rem' }}>Payment</th>
                <th style={{ padding: '0.875rem 1rem' }}>Status</th>
                <th style={{ padding: '0.875rem 1rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => {
                const bStyle = getStatusBadgeStyle(order.status);
                return (
                  <tr
                    key={order.id}
                    style={{ borderBottom: '1px solid #1e293b', cursor: 'pointer' }}
                    onClick={() => setSelectedOrder(order)}
                  >
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#60a5fa' }}>
                      {order.order_number}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                      {order.user_id.slice(0, 8)}...
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#cbd5e1' }}>
                      {new Date(order.created_at).toLocaleDateString()} {new Date(order.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', fontWeight: 700, color: '#f8fafc' }}>
                      ${Number(order.total_amount).toFixed(2)}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          color: order.payment_status === 'PAID' ? '#4ade80' : '#f87171',
                        }}
                      >
                        {order.payment_status} ({order.payment_method})
                      </span>
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      <span
                        style={{
                          padding: '0.2rem 0.5rem',
                          borderRadius: '0.25rem',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          backgroundColor: bStyle.bg,
                          color: bStyle.text,
                          border: `1px solid ${bStyle.border}`,
                        }}
                      >
                        {order.status}
                      </span>
                    </td>
                    <td
                      style={{ padding: '0.875rem 1rem', textAlign: 'right' }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.5rem' }}>
                        <button
                          onClick={() => setSelectedOrder(order)}
                          style={{
                            padding: '0.375rem 0.625rem',
                            borderRadius: '0.25rem',
                            backgroundColor: '#1e293b',
                            color: '#94a3b8',
                            border: '1px solid #334155',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            fontSize: '0.75rem',
                          }}
                          title="View Order Details"
                        >
                          <Eye size={14} />
                          Details
                        </button>

                        {/* Operational Actions */}
                        {canManage && order.status === 'PENDING' && (
                          <button
                            onClick={() => handleAction(order.id, 'CONFIRM', () => confirmOrder(order.id))}
                            disabled={actionLoadingId === `${order.id}-CONFIRM`}
                            style={{
                              padding: '0.375rem 0.625rem',
                              borderRadius: '0.25rem',
                              backgroundColor: '#2563eb',
                              color: '#ffffff',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}
                          >
                            <CheckCircle size={14} /> Confirm
                          </button>
                        )}

                        {canManage && order.status === 'CONFIRMED' && (
                          <button
                            onClick={() => handleAction(order.id, 'ALLOCATE', () => allocateOrderFefo(order.id))}
                            disabled={actionLoadingId === `${order.id}-ALLOCATE`}
                            style={{
                              padding: '0.375rem 0.625rem',
                              borderRadius: '0.25rem',
                              backgroundColor: '#4f46e5',
                              color: '#ffffff',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}
                          >
                            <Package size={14} /> FEFO
                          </button>
                        )}

                        {canManage && order.status === 'ALLOCATED' && (
                          <button
                            onClick={() => handleAction(order.id, 'PACK', () => packOrder(order.id))}
                            disabled={actionLoadingId === `${order.id}-PACK`}
                            style={{
                              padding: '0.375rem 0.625rem',
                              borderRadius: '0.25rem',
                              backgroundColor: '#9333ea',
                              color: '#ffffff',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}
                          >
                            Pack
                          </button>
                        )}

                        {canManage && order.status === 'PACKED' && (
                          <button
                            onClick={() => handleAction(order.id, 'DISPATCH', () => dispatchOrder(order.id))}
                            disabled={actionLoadingId === `${order.id}-DISPATCH`}
                            style={{
                              padding: '0.375rem 0.625rem',
                              borderRadius: '0.25rem',
                              backgroundColor: '#0891b2',
                              color: '#ffffff',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}
                          >
                            <Truck size={14} /> Ship
                          </button>
                        )}

                        {canManage && order.status === 'SHIPPED' && (
                          <button
                            onClick={() => handleAction(order.id, 'DELIVER', () => deliverOrder(order.id))}
                            disabled={actionLoadingId === `${order.id}-DELIVER`}
                            style={{
                              padding: '0.375rem 0.625rem',
                              borderRadius: '0.25rem',
                              backgroundColor: '#16a34a',
                              color: '#ffffff',
                              border: 'none',
                              cursor: 'pointer',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}
                          >
                            Deliver
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Order Detail Modal */}
      {selectedOrder && (
        <OrderDetailModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          onOrderUpdated={() => refetch()}
        />
      )}
    </div>
  );
};
