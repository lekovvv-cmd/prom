import { serviceDeskApiClient } from "@prom/api-client";
import type {
  ApprovalMetrics,
  AssigneeStats,
  BacklogBucket,
  DistributionItem,
  SlaMetrics,
  Summary,
  TimeMetrics,
} from "../model/types";

const query = (params: URLSearchParams) =>
  params.toString() ? `?${params}` : "";
export const getStatsSummary = (p: URLSearchParams) =>
  serviceDeskApiClient.request<Summary>(`/admin/stats/summary${query(p)}`);
export const getStatsDistribution = (
  kind: "statuses" | "services" | "categories",
  p: URLSearchParams,
) =>
  serviceDeskApiClient.request<DistributionItem[]>(
    `/admin/stats/${kind}${query(p)}`,
  );
export const getTimeMetrics = (p: URLSearchParams) =>
  serviceDeskApiClient.request<TimeMetrics>(`/admin/stats/times${query(p)}`);
export const getSlaMetrics = (p: URLSearchParams) =>
  serviceDeskApiClient.request<SlaMetrics>(`/admin/stats/sla${query(p)}`);
export const getBacklog = (p: URLSearchParams) =>
  serviceDeskApiClient.request<BacklogBucket[]>(
    `/admin/stats/backlog-aging${query(p)}`,
  );
export const getAssignees = (p: URLSearchParams) =>
  serviceDeskApiClient.request<AssigneeStats[]>(
    `/admin/stats/assignees${query(p)}`,
  );
export const getApprovalMetrics = (p: URLSearchParams) =>
  serviceDeskApiClient.request<ApprovalMetrics>(
    `/admin/stats/approvals${query(p)}`,
  );
