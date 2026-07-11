import { serviceDeskApiClient } from "../../../shared/api/client";
import type { ServiceDeskAttachment, ServiceDeskPriority, ServiceDeskTicket } from "../model/types";

export function getServiceDeskTicket(ticketId: string) {
  return serviceDeskApiClient.request<ServiceDeskTicket>(`/tickets/${ticketId}`);
}

export function getMyServiceDeskTickets(status?: string) {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
  return serviceDeskApiClient.request<ServiceDeskTicket[]>(`/me/tickets${suffix}`);
}

export function createServiceDeskDraft(payload: { service_id: string; template_version_id?: string; title: string; description: string; priority: ServiceDeskPriority; field_values: Record<string, unknown> }) {
  return serviceDeskApiClient.request<ServiceDeskTicket>("/tickets/drafts", { method: "POST", body: JSON.stringify(payload) });
}

export function updateServiceDeskDraft(ticketId: string, payload: { title?: string; description?: string; priority?: ServiceDeskPriority; field_values?: Record<string, unknown> }) {
  return serviceDeskApiClient.request<ServiceDeskTicket>(`/tickets/${ticketId}`, { method: "PATCH", body: JSON.stringify(payload) });
}

export function submitServiceDeskDraft(ticketId: string) {
  return serviceDeskApiClient.request<ServiceDeskTicket>(`/tickets/${ticketId}/submit`, { method: "POST", body: JSON.stringify({}) });
}

export function listServiceDeskAttachments(ticketId: string) {
  return serviceDeskApiClient.request<ServiceDeskAttachment[]>(`/tickets/${ticketId}/attachments`);
}

export function uploadServiceDeskFieldAttachment(ticketId: string, fieldKey: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return serviceDeskApiClient.request<ServiceDeskAttachment>(`/tickets/${ticketId}/fields/${encodeURIComponent(fieldKey)}/attachments`, { method: "POST", body: formData });
}
