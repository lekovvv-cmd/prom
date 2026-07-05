import type { User } from "../../user/model/types";

export type ReportPeriodStatus = "open" | "closed";

export type ReportPeriod = {
  id: string;
  title: string;
  starts_on: string | null;
  ends_on: string | null;
  status: ReportPeriodStatus;
  opened_by: string;
  opened_at: string;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type HalfYearReportPayload = {
  completed_work: string;
  project_results?: string | null;
  competencies_used?: string | null;
  difficulties?: string | null;
  next_period_plans?: string | null;
};

export type HalfYearReport = HalfYearReportPayload & {
  id: string;
  period_id: string;
  user_id: string;
  submitted_at: string;
  updated_at: string;
};

export type AdminHalfYearReport = HalfYearReport & {
  user: User;
  period: ReportPeriod;
};

export type CurrentReportState = {
  active_period: ReportPeriod | null;
  report: HalfYearReport | null;
};

export type ReportPeriodPayload = {
  title: string;
  starts_on?: string | null;
  ends_on?: string | null;
};
