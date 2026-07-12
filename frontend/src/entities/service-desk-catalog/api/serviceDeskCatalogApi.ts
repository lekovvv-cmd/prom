import { serviceDeskApiClient } from "../../../shared/api/client";
import type { ServiceDeskCategory, ServiceDeskPublishedForm, ServiceDeskService } from "../model/types";

export function getServiceDeskCategories(query = "") {
  const params = query.trim() ? `?q=${encodeURIComponent(query.trim())}` : "";
  return serviceDeskApiClient.request<ServiceDeskCategory[]>(`/categories${params}`, { auth: false });
}

export function getServiceDeskServices(categoryId = "", query = "") {
  const params = new URLSearchParams();
  if (categoryId) params.set("category_id", categoryId);
  if (query.trim()) params.set("q", query.trim());
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return serviceDeskApiClient.request<ServiceDeskService[]>(`/services${suffix}`, { auth: false });
}

export function getServiceDeskService(serviceId: string) {
  return serviceDeskApiClient.request<ServiceDeskService>(`/services/${serviceId}`, { auth: false });
}

export function getServiceDeskServiceForm(serviceId: string) {
  return serviceDeskApiClient.request<ServiceDeskPublishedForm>(`/services/${serviceId}/form`, { auth: false });
}
