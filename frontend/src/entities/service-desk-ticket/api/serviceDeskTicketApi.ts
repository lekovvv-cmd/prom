import { serviceDeskApiClient } from "../../../shared/api/client";
import { env } from "../../../shared/config/env";
import type { ServiceDeskAttachment, ServiceDeskPriority, ServiceDeskTicket } from "../model/types";

export function getServiceDeskTicket(ticketId: string) {
  return serviceDeskApiClient.request<ServiceDeskTicket>(`/tickets/${ticketId}`);
}

export function getServiceDeskTicketForm(ticketId: string) {
  return serviceDeskApiClient.request<import("../../service-desk-catalog/model/types").ServiceDeskPublishedForm>(`/tickets/${ticketId}/form`);
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

export function changeServiceDeskTicketPriority(ticketId: string, priority: ServiceDeskPriority, reason: string) {
  return serviceDeskApiClient.request<ServiceDeskTicket>(`/tickets/${ticketId}/priority`, {
    method: "PATCH",
    body: JSON.stringify({ priority, reason })
  });
}

export function listServiceDeskAttachments(ticketId: string) {
  return serviceDeskApiClient.request<ServiceDeskAttachment[]>(`/tickets/${ticketId}/attachments`);
}

export function deleteServiceDeskAttachment(ticketId: string, attachmentId: string) {
  return serviceDeskApiClient.request<void>(`/tickets/${ticketId}/attachments/${attachmentId}`, {
    method: "DELETE"
  });
}

export function uploadServiceDeskFieldAttachment(ticketId: string, fieldKey: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return serviceDeskApiClient.request<ServiceDeskAttachment>(`/tickets/${ticketId}/fields/${encodeURIComponent(fieldKey)}/attachments`, { method: "POST", body: formData });
}

export function listServiceDeskFieldAttachments(ticketId: string, fieldKey: string) {
  return serviceDeskApiClient.request<ServiceDeskAttachment[]>(`/tickets/${ticketId}/fields/${encodeURIComponent(fieldKey)}/attachments`);
}

export function uploadServiceDeskTicketAttachment(ticketId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return serviceDeskApiClient.request<ServiceDeskAttachment>(`/tickets/${ticketId}/attachments`, { method: "POST", body: formData });
}

export function listServiceDeskCommentAttachments(ticketId: string, commentId: string) {
  return serviceDeskApiClient.request<ServiceDeskAttachment[]>(`/tickets/${ticketId}/comments/${commentId}/attachments`);
}

export function uploadServiceDeskCommentAttachment(ticketId: string, commentId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return serviceDeskApiClient.request<ServiceDeskAttachment>(`/tickets/${ticketId}/comments/${commentId}/attachments`, { method: "POST", body: formData });
}

export function performServiceDeskTicketAction(ticketId: string, action: string, payload: Record<string, string> = {}) {
  const endpoint = `/tickets/${ticketId}/${action.replace("request_clarification", "request-clarification").replace("wait_external", "wait-external")}`;
  return serviceDeskApiClient.request<ServiceDeskTicket>(endpoint, { method: "POST", body: JSON.stringify(payload) });
}

export async function downloadServiceDeskAttachment(ticketId: string, attachmentId: string) {
  const response = await fetch(`${env.serviceDeskApiBaseUrl}/tickets/${ticketId}/attachments/${attachmentId}/download`, {
    headers: serviceDeskApiClient.getToken() ? { Authorization: `Bearer ${serviceDeskApiClient.getToken()}` } : undefined
  });
  if (!response.ok) throw new Error("Не удалось скачать файл");
  return response.blob();
}
