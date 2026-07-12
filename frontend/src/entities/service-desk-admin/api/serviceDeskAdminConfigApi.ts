import { serviceDeskApiClient } from "../../../shared/api/client";
import type { ServiceDeskCategory, ServiceDeskService, ServiceDeskTemplateField, ServiceDeskTemplateFieldType } from "../../service-desk-catalog/model/types";

export type AdminTemplateVersion = { id: string; service_id: string; version: number; status: "draft" | "published" | "archived"; approval_mode: "none" | "workflow"; system_settings: Record<string, unknown>; fields: ServiceDeskTemplateField[] };
export type AdminDictionaryItem = { id: string; dictionary_id: string; label: string; value: string; position: number; is_active: boolean };
export type AdminDictionary = { id: string; code: string; title: string; description: string | null; is_active: boolean; items: AdminDictionaryItem[] };
export type ApprovalConfiguration = { template_version_id: string; approval_mode: "none" | "workflow"; workflow: { id: string; name: string; is_active: boolean; stages: Array<{ id: string; title: string; position: number; decision_rule: "any" | "all"; approvers: Array<{ id: string; service_desk_user_id: string }> }> } | null };

export const listAdminCategories = (query = "") => serviceDeskApiClient.request<ServiceDeskCategory[]>(`/admin/categories${query ? `?q=${encodeURIComponent(query)}` : ""}`);
export const createAdminCategory = (payload: { title: string; description?: string; parent_id?: string | null }) => serviceDeskApiClient.request<ServiceDeskCategory>("/admin/categories", { method: "POST", body: JSON.stringify(payload) });
export const updateAdminCategory = (id: string, payload: Record<string, unknown>) => serviceDeskApiClient.request<ServiceDeskCategory>(`/admin/categories/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
export const listAdminServices = (query = "") => serviceDeskApiClient.request<ServiceDeskService[]>(`/admin/services${query ? `?q=${encodeURIComponent(query)}` : ""}`);
export const createAdminService = (payload: { category_id: string; title: string; short_description?: string; description?: string }) => serviceDeskApiClient.request<ServiceDeskService>("/admin/services", { method: "POST", body: JSON.stringify(payload) });
export const updateAdminService = (id: string, payload: Record<string, unknown>) => serviceDeskApiClient.request<ServiceDeskService>(`/admin/services/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
export const toggleAdminCatalogItem = (kind: "categories" | "services", id: string, active: boolean) => serviceDeskApiClient.request(kind === "categories" ? `/admin/categories/${id}/${active ? "restore" : "deactivate"}` : `/admin/services/${id}/${active ? "restore" : "deactivate"}`, { method: "POST", body: JSON.stringify({}) });

export const listAdminTemplateVersions = (serviceId: string) => serviceDeskApiClient.request<AdminTemplateVersion[]>(`/admin/services/${serviceId}/versions`);
export const createAdminTemplateVersion = (serviceId: string) => serviceDeskApiClient.request<AdminTemplateVersion>(`/admin/services/${serviceId}/versions`, { method: "POST", body: JSON.stringify({}) });
export const createAdminTemplateField = (versionId: string, payload: { key: string; label: string; field_type: ServiceDeskTemplateFieldType; is_required: boolean; position: number; options?: Array<{ label: string; value: string }>; placeholder?: string; help_text?: string; dictionary_code?: string; validation?: Record<string, unknown>; visibility_rules?: Record<string, unknown> | Array<Record<string, unknown>>; required_rules?: Record<string, unknown> | Array<Record<string, unknown>> }) => serviceDeskApiClient.request<ServiceDeskTemplateField>(`/admin/template-versions/${versionId}/fields`, { method: "POST", body: JSON.stringify(payload) });
export const updateAdminTemplateField = (fieldId: string, payload: Record<string, unknown>) => serviceDeskApiClient.request<ServiceDeskTemplateField>(`/admin/template-fields/${fieldId}`, { method: "PATCH", body: JSON.stringify(payload) });
export const reorderAdminTemplateFields = (versionId: string, fieldIds: string[]) => serviceDeskApiClient.request<ServiceDeskTemplateField[]>(`/admin/template-versions/${versionId}/reorder-fields`, { method: "POST", body: JSON.stringify({ field_ids: fieldIds }) });
export const previewAdminTemplateVersion = (versionId: string) => serviceDeskApiClient.request<{ template_version: AdminTemplateVersion; fields: ServiceDeskTemplateField[] }>(`/admin/template-versions/${versionId}/preview`);
export const deleteAdminTemplateField = (fieldId: string) => serviceDeskApiClient.request<void>(`/admin/template-fields/${fieldId}`, { method: "DELETE" });
export const publishAdminTemplateVersion = (versionId: string) => serviceDeskApiClient.request<AdminTemplateVersion>(`/admin/template-versions/${versionId}/publish`, { method: "POST", body: JSON.stringify({}) });

export const listAdminDictionaries = () => serviceDeskApiClient.request<AdminDictionary[]>("/admin/dictionaries");
export const createAdminDictionary = (payload: { code: string; title: string; description?: string }) => serviceDeskApiClient.request<AdminDictionary>("/admin/dictionaries", { method: "POST", body: JSON.stringify(payload) });
export const updateAdminDictionary = (id: string, payload: Record<string, unknown>) => serviceDeskApiClient.request<AdminDictionary>(`/admin/dictionaries/${id}`, { method: "PATCH", body: JSON.stringify(payload) });
export const createAdminDictionaryItem = (id: string, payload: { label: string; value: string; position: number }) => serviceDeskApiClient.request<AdminDictionaryItem>(`/admin/dictionaries/${id}/items`, { method: "POST", body: JSON.stringify(payload) });
export const updateAdminDictionaryItem = (id: string, payload: Record<string, unknown>) => serviceDeskApiClient.request<AdminDictionaryItem>(`/admin/dictionary-items/${id}`, { method: "PATCH", body: JSON.stringify(payload) });

export const getAdminApprovalConfiguration = (versionId: string) => serviceDeskApiClient.request<ApprovalConfiguration>(`/admin/template-versions/${versionId}/approval-workflow`);
export const configureAdminApproval = (versionId: string, payload: { approval_mode: "none" | "workflow"; name: string; is_active: boolean }) => serviceDeskApiClient.request<ApprovalConfiguration>(`/admin/template-versions/${versionId}/approval-workflow`, { method: "PUT", body: JSON.stringify(payload) });
export const createAdminApprovalStage = (workflowId: string, payload: { title: string; decision_rule: "any" | "all"; position?: number }) => serviceDeskApiClient.request<ApprovalConfiguration>(`/admin/approval-workflows/${workflowId}/stages`, { method: "POST", body: JSON.stringify(payload) });
export const addAdminApprover = (stageId: string, serviceDeskUserId: string) => serviceDeskApiClient.request<ApprovalConfiguration>(`/admin/approval-stages/${stageId}/approvers`, { method: "POST", body: JSON.stringify({ service_desk_user_id: serviceDeskUserId }) });
export const updateAdminApprovalStage = (stageId: string, payload: { title?: string; decision_rule?: "any" | "all"; position?: number }) => serviceDeskApiClient.request<ApprovalConfiguration>(`/admin/approval-stages/${stageId}`, { method: "PATCH", body: JSON.stringify(payload) });
export const deleteAdminApprovalStage = (stageId: string) => serviceDeskApiClient.request<void>(`/admin/approval-stages/${stageId}`, { method: "DELETE" });
export const reorderAdminApprovalStages = (workflowId: string, stageIds: string[]) => serviceDeskApiClient.request<ApprovalConfiguration>(`/admin/approval-workflows/${workflowId}/reorder-stages`, { method: "POST", body: JSON.stringify({ stage_ids: stageIds }) });
export const deleteAdminApprover = (approverId: string) => serviceDeskApiClient.request<void>(`/admin/approval-stage-approvers/${approverId}`, { method: "DELETE" });
