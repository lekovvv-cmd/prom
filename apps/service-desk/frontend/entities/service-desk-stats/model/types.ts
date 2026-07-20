export type DistributionItem = { id: string; label: string; count: number };
export type Summary = {
  created: number;
  closed_in_period: number;
  current_backlog: number;
  submitted: number;
  pending_approval: number;
  approved_in_period: number;
  rejected_in_period: number;
  assigned: number;
  in_progress: number;
  waiting_requester: number;
  waiting_external: number;
  resolved: number;
  closed: number;
  cancelled_in_period: number;
  priorities: DistributionItem[];
};
type DurationStats = {
  average_seconds: number | null;
  median_seconds: number | null;
  p90_seconds: number | null;
  sample_size: number;
};
export type TimeMetrics = {
  time_to_approval: DurationStats;
  time_to_assignment: DurationStats;
  first_response_time: DurationStats;
  resolution_time: DurationStats;
  close_after_resolution_time: DurationStats;
};
export type SlaMetrics = {
  response_compliance_percent: number | null;
  resolution_compliance_percent: number | null;
  response_breaches: number;
  resolution_breaches: number;
  active_near_breach: number;
  active_breached: number;
};
export type BacklogBucket = { code: string; label: string; count: number };
export type AssigneeStats = {
  user_id: string;
  display_name: string;
  is_active: boolean;
  currently_assigned: number;
  in_progress: number;
  waiting: number;
  resolved_in_period: number;
  closed_in_period: number;
  breached_tickets: number;
  median_resolution_seconds: number | null;
};
export type ApprovalMetrics = {
  pending_approval_stages: number;
  stage_duration: DurationStats;
  rejection_rate_percent: number | null;
};
