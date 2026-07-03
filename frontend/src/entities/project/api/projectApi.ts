import { apiClient } from "../../../shared/api/client";
import type { Attachment, Paginated, Project, ProjectDetails, ProjectListParams, ProjectMutationPayload } from "../model/types";

function toQuery(params: ProjectListParams = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function getProjects(params?: ProjectListParams) {
  return apiClient.request<Paginated<Project>>(`/projects${toQuery(params)}`, { auth: false });
}

export function getProject(projectId: string) {
  return apiClient.request<ProjectDetails>(`/projects/${projectId}`, { auth: false });
}

export function getAdminProjects(params?: ProjectListParams) {
  return apiClient.request<Paginated<Project>>(`/admin/projects${toQuery(params)}`);
}

export function getAdminProject(projectId: string) {
  return apiClient.request<ProjectDetails>(`/admin/projects/${projectId}`);
}

export function createAdminProject(payload: ProjectMutationPayload) {
  return apiClient.request<ProjectDetails>("/admin/projects", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateAdminProject(projectId: string, payload: Partial<ProjectMutationPayload>) {
  return apiClient.request<ProjectDetails>(`/admin/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function archiveAdminProject(projectId: string) {
  return apiClient.request<{ ok: boolean }>(`/admin/projects/${projectId}`, {
    method: "DELETE"
  });
}

export function deleteArchivedAdminProject(projectId: string) {
  return apiClient.request<{ ok: boolean }>(`/admin/projects/${projectId}`, {
    method: "DELETE"
  });
}

export function restoreArchivedAdminProject(projectId: string) {
  return apiClient.request<ProjectDetails>(`/admin/projects/${projectId}/restore`, {
    method: "PATCH"
  });
}

export function uploadAdminProjectAttachment(projectId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.request<Attachment>(`/admin/projects/${projectId}/attachments`, {
    method: "POST",
    body: formData
  });
}
