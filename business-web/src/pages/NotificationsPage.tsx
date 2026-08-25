/**
 * AVENZO Business Web — Notifications Page
 * View system alert notifications, expiry warnings, and mark items as read.
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getMyNotificationsApi, markNotificationReadApi } from '../api/notifications.api';
import { Bell, Check, AlertTriangle, Info } from 'lucide-react';

export const NotificationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [unreadOnly, setUnreadOnly] = useState(false);

  const { data: notifRes, isLoading, isError } = useQuery({
    queryKey: ['myNotifications', unreadOnly],
    queryFn: () => getMyNotificationsApi(unreadOnly),
  });

  const markReadMutation = useMutation({
    mutationFn: (id: string) => markNotificationReadApi(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myNotifications'] });
    },
  });

  const notifications = notifRes?.data || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0f172a', margin: 0 }}>
            System & Operational Notifications
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: '0.25rem 0 0' }}>
            Real-time notifications, automated expiry alerts, and inventory warnings.
          </p>
        </div>

        <button
          onClick={() => setUnreadOnly(!unreadOnly)}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '0.375rem',
            border: '1px solid #cbd5e1',
            backgroundColor: unreadOnly ? '#dbeafe' : '#ffffff',
            color: unreadOnly ? '#1e40af' : '#475569',
            fontWeight: 600,
            cursor: 'pointer',
            fontSize: '0.875rem',
          }}
        >
          {unreadOnly ? 'Showing Unread Only' : 'Show All Notifications'}
        </button>
      </div>

      {/* Notifications List */}
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '0.5rem',
          border: '1px solid #e2e8f0',
          overflow: 'hidden',
        }}
      >
        {isLoading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>Loading notifications...</div>
        ) : isError ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#ef4444' }}>
            Failed to load notifications. Please try again.
          </div>
        ) : notifications.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#64748b' }}>
            <Bell size={36} style={{ margin: '0 auto 0.5rem', opacity: 0.5 }} />
            <p>No notifications found.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {notifications.map((n) => (
              <div
                key={n.id}
                style={{
                  padding: '1.25rem 1.5rem',
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: '1rem',
                  backgroundColor: n.is_read ? '#ffffff' : '#f8fafc',
                  borderBottom: '1px solid #f1f5f9',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                  <div style={{ marginTop: '0.125rem' }}>
                    {n.notification_type.includes('EXPIRY') ? (
                      <AlertTriangle size={20} color="#d97706" />
                    ) : (
                      <Info size={20} color="#2563eb" />
                    )}
                  </div>
                  <div>
                    <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#0f172a', margin: 0 }}>
                      {n.title}
                    </h4>
                    <p style={{ fontSize: '0.875rem', color: '#475569', margin: '0.25rem 0' }}>{n.body}</p>
                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                      {new Date(n.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>

                {!n.is_read && (
                  <button
                    onClick={() => markReadMutation.mutate(n.id)}
                    disabled={markReadMutation.isPending}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      padding: '0.375rem 0.75rem',
                      borderRadius: '0.25rem',
                      border: '1px solid #cbd5e1',
                      backgroundColor: '#ffffff',
                      color: '#2563eb',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    <Check size={14} />
                    Mark Read
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
