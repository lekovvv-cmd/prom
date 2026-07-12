export type ServiceDeskTicketStatus =
  | "draft"
  | "submitted"
  | "pending_approval"
  | "approved"
  | "rejected"
  | "assigned"
  | "in_progress"
  | "waiting_requester"
  | "waiting_external"
  | "resolved"
  | "closed"
  | "cancelled";

export type ServiceDeskPriority = "low" | "medium" | "high" | "critical";
export type ServiceDeskApprovalStatus = "pending" | "approved" | "rejected" | "skipped";
export type ServiceDeskAllowedAction = "approve" | "reject" | "assign" | "reassign" | "start" | "request_clarification" | "wait_external" | "resume" | "resolve" | "close" | "cancel";

export type ServiceDeskTicketUser = {
  id: string;
  display_name: string;
  email: string;
};

export type ServiceDeskTicketApproval = {
  id: string;
  ticket_approval_stage_id: string;
  approver_user_id: string;
  approver_display_name: string;
  status: ServiceDeskApprovalStatus;
  decision_comment: string | null;
  decided_at: string | null;
  created_at: string;
};

export type ServiceDeskTicketApprovalStage = {
  id: string;
  ticket_id: string;
  position: number;
  title: string;
  decision_rule: "any" | "all";
  status: ServiceDeskApprovalStatus;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  approvals: ServiceDeskTicketApproval[];
};

export type ServiceDeskTicketHistory = {
  id: string;
  ticket_id: string;
  event_type: string;
  actor_user_id: string | null;
  message: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type ServiceDeskTicketFieldSnapshot = {
  key: string;
  label: string;
  type: string;
  raw_value: unknown;
  display_value: string;
};

export type ServiceDeskTicketComment = {
  id: string;
  ticket_id: string;
  author_user_id: string;
  author: ServiceDeskTicketUser;
  body: string;
  visibility: "public" | "internal";
  created_at: string;
  updated_at: string | null;
};

export type ServiceDeskTicket = {
  id: string;
  number: string | null;
  service_id: string;
  service: {
    id: string;
    title: string;
    category: { id: string; title: string };
  };
  template_version_id: string;
  requester_user_id: string;
  requester: ServiceDeskTicketUser;
  assignee_user_id: string | null;
  assignee: ServiceDeskTicketUser | null;
  title: string;
  description: string | null;
  status: ServiceDeskTicketStatus;
  priority: ServiceDeskPriority;
  field_values: Record<string, unknown>;
  field_snapshot?: ServiceDeskTicketFieldSnapshot[];
  routing_snapshot?: Record<string, unknown> | null;
  sla_snapshot?: Record<string, unknown> | null;
  sla_policy_id?: string | null;
  first_response_due_at?: string | null;
  resolution_due_at?: string | null;
  first_response_at?: string | null;
  response_breached_at?: string | null;
  resolution_breached_at?: string | null;
  is_response_breached?: boolean;
  is_resolution_breached?: boolean;
  paused_seconds?: number;
  submitted_at: string | null;
  approval_started_at: string | null;
  approved_at: string | null;
  rejected_at: string | null;
  assigned_at: string | null;
  work_started_at: string | null;
  resolved_at: string | null;
  closed_at: string | null;
  cancelled_at: string | null;
  resolution_summary: string | null;
  cancellation_reason: string | null;
  approval_stages: ServiceDeskTicketApprovalStage[];
  comments: ServiceDeskTicketComment[];
  allowed_actions: ServiceDeskAllowedAction[];
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  history: ServiceDeskTicketHistory[];
};

export type ServiceDeskAttachment = {
  id: string;
  owner_type: "service_desk_ticket" | "service_desk_comment" | "service_desk_field_value";
  owner_id: string;
  ticket_id: string;
  field_key: string | null;
  file_name: string;
  content_type: string | null;
  size_bytes: number;
  uploaded_by_user_id: string;
  created_at: string;
};
