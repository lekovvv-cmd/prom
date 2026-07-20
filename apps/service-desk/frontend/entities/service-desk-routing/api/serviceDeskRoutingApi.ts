import { serviceDeskApiClient } from "@prom/api-client";
import type {
  ServiceDeskRoutingAssignee,
  ServiceDeskRoutingCatalogOptions,
  ServiceDeskRoutingRule,
  ServiceDeskRoutingRulePayload,
} from "../model/types";

export function getServiceDeskRoutingRules() {
  return serviceDeskApiClient.request<ServiceDeskRoutingRule[]>(
    "/admin/routing-rules",
  );
}

export function getServiceDeskRoutingCandidates() {
  return serviceDeskApiClient.request<ServiceDeskRoutingAssignee[]>(
    "/admin/routing-rules/candidates",
  );
}

export function getServiceDeskRoutingCatalogOptions() {
  return serviceDeskApiClient.request<ServiceDeskRoutingCatalogOptions>(
    "/admin/routing-rules/catalog-options",
  );
}

export function createServiceDeskRoutingRule(
  payload: ServiceDeskRoutingRulePayload,
) {
  return serviceDeskApiClient.request<ServiceDeskRoutingRule>(
    "/admin/routing-rules",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function updateServiceDeskRoutingRule(
  ruleId: string,
  payload: Partial<ServiceDeskRoutingRulePayload>,
) {
  return serviceDeskApiClient.request<ServiceDeskRoutingRule>(
    `/admin/routing-rules/${ruleId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}

export function deleteServiceDeskRoutingRule(ruleId: string) {
  return serviceDeskApiClient.request<void>(`/admin/routing-rules/${ruleId}`, {
    method: "DELETE",
  });
}

export function reorderServiceDeskRoutingRules(ruleIds: string[]) {
  return serviceDeskApiClient.request<ServiceDeskRoutingRule[]>(
    "/admin/routing-rules/reorder",
    {
      method: "POST",
      body: JSON.stringify({ rule_ids: ruleIds }),
    },
  );
}
