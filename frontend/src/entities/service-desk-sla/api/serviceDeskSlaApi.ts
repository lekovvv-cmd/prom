import { serviceDeskApiClient } from "../../../shared/api/client";
import type {
  BusinessCalendar,
  BusinessCalendarPayload,
  EscalationRule,
  EscalationRulePayload,
  SlaBinding,
  SlaBindingPayload,
  SlaPolicy,
  SlaPolicyPayload,
  SlaRecipient
} from "../model/types";

const request = serviceDeskApiClient.request.bind(serviceDeskApiClient);
export const getSlaCalendars = () => request<BusinessCalendar[]>("/admin/sla/calendars");
export const createSlaCalendar = (payload: BusinessCalendarPayload) => request<BusinessCalendar>("/admin/sla/calendars", { method: "POST", body: JSON.stringify(payload) });
export const updateSlaCalendar = (calendarId: string, payload: BusinessCalendarPayload) => request<BusinessCalendar>(`/admin/sla/calendars/${calendarId}`, { method: "PATCH", body: JSON.stringify(payload) });
export const getSlaPolicies = () => request<SlaPolicy[]>("/admin/sla/policies");
export const createSlaPolicy = (payload: SlaPolicyPayload) => request<SlaPolicy>("/admin/sla/policies", { method: "POST", body: JSON.stringify(payload) });
export const updateSlaPolicy = (policyId: string, payload: SlaPolicyPayload) => request<SlaPolicy>(`/admin/sla/policies/${policyId}`, { method: "PATCH", body: JSON.stringify(payload) });
export const getSlaBindings = () => request<SlaBinding[]>("/admin/sla/bindings");
export const createSlaBinding = (payload: SlaBindingPayload) => request<SlaBinding>("/admin/sla/bindings", { method: "POST", body: JSON.stringify(payload) });
export const updateSlaBinding = (bindingId: string, payload: SlaBindingPayload) => request<SlaBinding>(`/admin/sla/bindings/${bindingId}`, { method: "PATCH", body: JSON.stringify(payload) });
export const getEscalations = () => request<EscalationRule[]>("/admin/sla/escalations");
export const createEscalation = (policyId: string, payload: EscalationRulePayload) => request<EscalationRule>(`/admin/sla/policies/${policyId}/escalations`, { method: "POST", body: JSON.stringify(payload) });
export const updateEscalation = (ruleId: string, payload: EscalationRulePayload) => request<EscalationRule>(`/admin/sla/escalations/${ruleId}`, { method: "PATCH", body: JSON.stringify(payload) });
export const deleteEscalation = (ruleId: string) => request<void>(`/admin/sla/escalations/${ruleId}`, { method: "DELETE" });
export const getSlaRecipients = () => request<SlaRecipient[]>("/admin/sla/recipients");
