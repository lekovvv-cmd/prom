import type { ProjectResponse, ProjectResponsePayload } from "../../../entities/project-response/model/types";
import { apiClient } from "../../../shared/api/client";

export function submitProjectResponse(projectId: string, payload: ProjectResponsePayload) {
  return apiClient.request<ProjectResponse>(`/projects/${projectId}/responses`, {
    method: "POST",
    auth: false,
    body: JSON.stringify(payload)
  });
}
