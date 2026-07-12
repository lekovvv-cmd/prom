import { serviceDeskApiClient } from "../../../shared/api/client";
import type { ServiceDeskUser } from "../model/types";

export function getCurrentServiceDeskUser() {
  return serviceDeskApiClient.request<ServiceDeskUser>("/me");
}
export function getServiceDeskAccessStatus() {
  return serviceDeskApiClient.request<{ has_access: boolean }>("/access/status");
}
export type ServiceDeskUserOption = { id: string; display_name: string; department: string | null; position: string | null };
export function getServiceDeskUserOptions(capability?: string) {
  const suffix = capability ? `?capability=${encodeURIComponent(capability)}` : "";
  return serviceDeskApiClient.request<ServiceDeskUserOption[]>(`/users/options${suffix}`);
}
export type ServiceDeskUserPage = { items: ServiceDeskUser[]; page: number; page_size: number; total: number; pages: number };
export const getAccessUsers = (params: URLSearchParams) => serviceDeskApiClient.request<ServiceDeskUserPage>(`/admin/access/users?${params}`);
export const createAccessUser = (payload: Record<string, unknown>) => serviceDeskApiClient.request<ServiceDeskUser>("/admin/access/users", { method: "POST", body: JSON.stringify(payload) });
export const updateAccessUser = (id: string, payload: Record<string, unknown>) => serviceDeskApiClient.request<ServiceDeskUser>(`/admin/access/users/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
export const replaceUserCapabilities = (id: string, capabilities: string[]) => serviceDeskApiClient.request<ServiceDeskUser>(`/admin/access/users/${id}/capabilities`, { method: "PUT", body: JSON.stringify({ capabilities }) });
export const setAccessUserActive = (id: string, active: boolean) => serviceDeskApiClient.request<ServiceDeskUser>(`/admin/access/users/${id}/${active ? "activate" : "deactivate"}`, { method: "POST" });
