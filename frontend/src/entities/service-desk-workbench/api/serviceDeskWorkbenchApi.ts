import { serviceDeskApiClient } from "../../../shared/api/client";
import type { CatalogOption, WorkbenchCounters, WorkbenchPage, WorkbenchUserOption } from "../model/types";

export function getWorkbenchTickets(params: URLSearchParams) {
  return serviceDeskApiClient.request<WorkbenchPage>(`/workbench/tickets?${params}`);
}
export function getWorkbenchCounters() {
  return serviceDeskApiClient.request<WorkbenchCounters>("/workbench/counters");
}
export function getWorkbenchUsers(eligibleAssignees = false) {
  return serviceDeskApiClient.request<WorkbenchUserOption[]>(`/workbench/users?eligible_assignees=${eligibleAssignees}`);
}
export function getWorkbenchCategories() {
  return serviceDeskApiClient.request<CatalogOption[]>("/categories");
}
export function getWorkbenchServices(categoryId = "") {
  return serviceDeskApiClient.request<CatalogOption[]>(`/services${categoryId ? `?category_id=${categoryId}` : ""}`);
}
export function performWorkbenchAction(ticketId: string, action: string, payload: Record<string, string> = {}, approvalId?: string | null) {
  const endpoint = action === "approve" || action === "reject"
    ? `/tickets/${ticketId}/approvals/${approvalId}/${action}`
    : `/tickets/${ticketId}/${action.replace("request_clarification", "request-clarification").replace("wait_external", "wait-external")}`;
  return serviceDeskApiClient.request(endpoint, { method: "POST", body: JSON.stringify(payload) });
}
