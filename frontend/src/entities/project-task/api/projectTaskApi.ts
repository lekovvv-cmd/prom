import { apiClient } from "../../../shared/api/client";
import type {
  ProjectStage,
  ProjectStagePayload,
  ProjectStageWithTasks,
  ProjectTask,
  ProjectTaskPayload,
  ProjectTaskStatus
} from "../model/types";
import type { Attachment } from "../../project/model/types";

export function getAdminProjectStages(projectId: string) {
  return apiClient.request<ProjectStageWithTasks[]>(`/admin/projects/${projectId}/stages`);
}

export function createAdminProjectStage(projectId: string, payload: ProjectStagePayload) {
  return apiClient.request<ProjectStage>(`/admin/projects/${projectId}/stages`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateAdminProjectStage(projectId: string, stageId: string, payload: Partial<ProjectStagePayload>) {
  return apiClient.request<ProjectStage>(`/admin/projects/${projectId}/stages/${stageId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function createAdminProjectTask(projectId: string, payload: ProjectTaskPayload) {
  return apiClient.request<ProjectTask>(`/admin/projects/${projectId}/tasks`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateAdminProjectTask(projectId: string, taskId: string, payload: Partial<ProjectTaskPayload>) {
  return apiClient.request<ProjectTask>(`/admin/projects/${projectId}/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function getMyProjectTasks(projectId: string) {
  return apiClient.request<ProjectTask[]>(`/me/projects/${projectId}/tasks`);
}

export function updateMyProjectTaskStatus(taskId: string, status: ProjectTaskStatus) {
  return apiClient.request<ProjectTask>(`/me/project-tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify({ status })
  });
}

export function uploadProjectTaskAttachment(taskId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return apiClient.request<Attachment>(`/project-tasks/${taskId}/attachments`, {
    method: "POST",
    body: formData
  });
}
