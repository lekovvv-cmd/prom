import { serviceDeskApiClient } from "../../../shared/api/client";
import type { ServiceDeskContextualCounters, ServiceDeskNotification } from "../model/types";

export function getServiceDeskNotifications(limit = 30) {
  return serviceDeskApiClient.request<ServiceDeskNotification[]>(`/notifications?limit=${limit}`);
}

export function getServiceDeskUnreadCount() {
  return serviceDeskApiClient.request<{ count: number }>("/notifications/unread-count");
}

export function markServiceDeskNotificationRead(notificationId: string) {
  return serviceDeskApiClient.request<ServiceDeskNotification>(`/notifications/${notificationId}/read`, {
    method: "POST"
  });
}

export function markAllServiceDeskNotificationsRead() {
  return serviceDeskApiClient.request<{ marked_read: number }>("/notifications/read-all", {
    method: "POST"
  });
}

export function getServiceDeskContextualCounters() {
  return serviceDeskApiClient.request<ServiceDeskContextualCounters>("/notifications/contextual-counters");
}
