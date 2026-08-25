/**
 * AVENZO Business Web — Notifications API Wrapper
 * Matches FastAPI backend routes (/api/v1/notifications)
 */

import { apiGet, apiPost, ApiResponse } from './client';

export interface NotificationRecord {
  id: string;
  user_id: string;
  notification_type: string;
  title: string;
  body: string;
  payload_json?: string;
  status: string;
  is_read: boolean;
  created_at: string;
  sent_at?: string;
}

export async function getMyNotificationsApi(unreadOnly = false): Promise<ApiResponse<NotificationRecord[]>> {
  return apiGet<NotificationRecord[]>('/notifications', { unread_only: unreadOnly });
}

export async function markNotificationReadApi(id: string): Promise<ApiResponse<NotificationRecord>> {
  return apiPost<NotificationRecord>(`/notifications/${id}/read`);
}
