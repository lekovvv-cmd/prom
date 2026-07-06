import { apiClient } from "../../../shared/api/client";
import type {
  Attachment,
  Paginated,
  Project,
  ProjectCandidate,
  ProjectCandidateParams,
  ProjectDetails,
  ProjectListParams,
  ProjectRecommendation,
  ProjectMutationPayload
} from "../model/types";

function toQuery(params: ProjectListParams | ProjectCandidateParams = {}) {
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

export function getProjectRecommendations(limit = 5) {
  return apiClient.request<ProjectRecommendation[]>(`/projects/recommendations?limit=${limit}`);
}

export function getAdminProjects(params?: ProjectListParams) {
  return apiClient.request<Paginated<Project>>(`/admin/projects${toQuery(params)}`);
}

export function getAdminProject(projectId: string) {
  return apiClient.request<ProjectDetails>(`/admin/projects/${projectId}`);
}

export function getMyProjects(params?: ProjectListParams) {
  return apiClient.request<Paginated<Project>>(`/me/projects${toQuery(params)}`);
}

export function getMyProject(projectId: string) {
  return apiClient.request<ProjectDetails>(`/me/projects/${projectId}`);
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

export function getAdminProjectCandidates(projectId: string, params?: ProjectCandidateParams) {
  return apiClient.request<Paginated<ProjectCandidate>>(`/admin/projects/${projectId}/candidates${toQuery(params)}`);
}

export function addAdminProjectMember(projectId: string, userId: string) {
  return apiClient.request<ProjectDetails>(`/admin/projects/${projectId}/members/${userId}`, {
    method: "POST"
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
