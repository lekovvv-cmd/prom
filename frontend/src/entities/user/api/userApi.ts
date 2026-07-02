import type { User } from "../model/types";
import { apiClient } from "../../../shared/api/client";

export function getMe() {
  return apiClient.request<User>("/me");
}
