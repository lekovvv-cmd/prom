import type {
  ProjectResponse,
  ProjectResponsePayload,
} from "../../../entities/project-response/model/types";
import { uploadProjectResponseAttachment } from "../../../entities/project-response/api/projectResponseApi";
import { apiClient } from "@prom/api-client";

function submitProjectResponse(
  projectId: string,
  payload: ProjectResponsePayload,
) {
  return apiClient.request<ProjectResponse>(
    `/projects/${projectId}/responses`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function submitProjectResponseWithFiles(
  projectId: string,
  payload: ProjectResponsePayload,
  files: File[],
) {
  const response = await submitProjectResponse(projectId, payload);
  await Promise.all(
    files.map((file) =>
      uploadProjectResponseAttachment(projectId, response.id, file),
    ),
  );
  return response;
}
