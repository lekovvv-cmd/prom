import type { User, UserProfilePayload } from "../model/types";
import { apiClient } from "../../../shared/api/client";

export function getMe() {
  return apiClient.request<User>("/me");
}

export function getAdminUsers() {
  return apiClient.request<User[]>("/admin/users");
}

export function getUserDirectory(search?: string) {
  const query = search ? `?${new URLSearchParams({ search }).toString()}` : "";
  return apiClient.request<User[]>(`/users/directory${query}`);
}

export function updateMyProfile(payload: UserProfilePayload) {
  return apiClient.request<User>("/me/profile", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}
