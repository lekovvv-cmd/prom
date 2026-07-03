import type { User } from "../model/types";
import { apiClient } from "../../../shared/api/client";

export function getMe() {
  return apiClient.request<User>("/me");
}

export function getAdminUsers() {
  return apiClient.request<User[]>("/admin/users");
}
