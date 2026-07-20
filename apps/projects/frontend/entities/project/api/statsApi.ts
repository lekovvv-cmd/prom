import { apiClient } from "@prom/api-client";
import type { AdminStats } from "../model/statsTypes";

export function getAdminStats() {
  return apiClient.request<AdminStats>("/admin/stats");
}
