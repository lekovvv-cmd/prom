import type {
  AdminHalfYearReport,
  CurrentReportState,
  HalfYearReport,
  HalfYearReportPayload,
  ReportPeriod,
  ReportPeriodPayload
} from "../model/types";
import { apiClient } from "../../../shared/api/client";

export function getCurrentReportState() {
  return apiClient.request<CurrentReportState>("/reports/current");
}

export function submitCurrentReport(payload: HalfYearReportPayload) {
  return apiClient.request<HalfYearReport>("/reports/current", {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function getAdminReportPeriods() {
  return apiClient.request<ReportPeriod[]>("/admin/reports/periods");
}

export function openAdminReportPeriod(payload: ReportPeriodPayload) {
  return apiClient.request<ReportPeriod>("/admin/reports/periods", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function closeAdminReportPeriod(periodId: string) {
  return apiClient.request<ReportPeriod>(`/admin/reports/periods/${periodId}/close`, {
    method: "PATCH"
  });
}

export function getAdminReports(periodId?: string | null) {
  const query = periodId ? `?${new URLSearchParams({ period_id: periodId }).toString()}` : "";
  return apiClient.request<AdminHalfYearReport[]>(`/admin/reports${query}`);
}
