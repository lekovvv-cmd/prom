import { apiClient } from "@prom/api-client";
import type { ProjectUser, ProjectUserProfilePayload } from "../model/types";

export function getProjectProfile() {
  return apiClient.request<ProjectUser>("/me");
}

export function getProjectAdminUsers() {
  return apiClient.request<ProjectUser[]>("/admin/users");
}

export function getProjectUserDirectory(search?: string) {
  const query = search ? `?${new URLSearchParams({ search }).toString()}` : "";
  return apiClient.request<ProjectUser[]>(`/users/directory${query}`);
}

export function updateProjectProfile(payload: ProjectUserProfilePayload) {
  return apiClient.request<ProjectUser>("/me/profile", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
