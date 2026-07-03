import { apiClient } from "../../../shared/api/client";
import type { Attachment, Paginated } from "../../project/model/types";
import type { ProjectResponse, ProjectResponseStatus } from "../model/types";

type ResponseListParams = {
  project_id?: string;
  status?: ProjectResponseStatus | "";
  search?: string;
  limit?: number;
  offset?: number;
};

function toQuery(params: ResponseListParams = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value));
    }
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

export function getAdminResponses(params?: ResponseListParams) {
  return apiClient.request<Paginated<ProjectResponse>>(`/admin/responses${toQuery(params)}`);
}

export function getMyResponses(params?: Pick<ResponseListParams, "limit" | "offset">) {
  return apiClient.request<Paginated<ProjectResponse>>(`/me/responses${toQuery(params)}`);
}

export function updateAdminResponseStatus(responseId: string, status: ProjectResponseStatus) {
  return apiClient.request<ProjectResponse>(`/admin/responses/${responseId}`, {
    method: "PATCH",
    body: JSON.stringify({ status })
  });
}

export function deleteAdminResponse(responseId: string) {
  return apiClient.request<{ ok: boolean }>(`/admin/responses/${responseId}`, {
    method: "DELETE"
  });
}

export function withdrawMyResponse(responseId: string) {
  return apiClient.request<ProjectResponse>(`/me/responses/${responseId}`, {
    method: "DELETE"
  });
}

export function uploadProjectResponseAttachment(projectId: string, responseId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.request<Attachment>(`/projects/${projectId}/responses/${responseId}/attachments`, {
    method: "POST",
    body: formData
  });
}
