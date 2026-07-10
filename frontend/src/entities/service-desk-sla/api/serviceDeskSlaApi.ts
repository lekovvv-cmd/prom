import { serviceDeskApiClient } from "../../../shared/api/client";
import type { BusinessCalendar, EscalationRule, SlaBinding, SlaPolicy } from "../model/types";

const request = serviceDeskApiClient.request.bind(serviceDeskApiClient);
export const getSlaCalendars = () => request<BusinessCalendar[]>("/admin/sla/calendars");
export const createSlaCalendar = (payload: Omit<BusinessCalendar, "id">) => request<BusinessCalendar>("/admin/sla/calendars", { method: "POST", body: JSON.stringify(payload) });
export const getSlaPolicies = () => request<SlaPolicy[]>("/admin/sla/policies");
export const createSlaPolicy = (payload: Omit<SlaPolicy, "id">) => request<SlaPolicy>("/admin/sla/policies", { method: "POST", body: JSON.stringify(payload) });
export const getSlaBindings = () => request<SlaBinding[]>("/admin/sla/bindings");
export const createSlaBinding = (payload: Omit<SlaBinding, "id">) => request<SlaBinding>("/admin/sla/bindings", { method: "POST", body: JSON.stringify(payload) });
export const getEscalations = () => request<EscalationRule[]>("/admin/sla/escalations");
export const createEscalation = (policyId: string, payload: Omit<EscalationRule, "id" | "sla_policy_id">) => request<EscalationRule>(`/admin/sla/policies/${policyId}/escalations`, { method: "POST", body: JSON.stringify(payload) });
