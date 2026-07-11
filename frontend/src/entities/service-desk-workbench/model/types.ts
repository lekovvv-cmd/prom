import type { ServiceDeskAllowedAction, ServiceDeskPriority, ServiceDeskTicketStatus } from "../../service-desk-ticket/model/types";

export type WorkbenchSlaState = "no_sla" | "on_track" | "paused" | "warning" | "breached";
export type WorkbenchQuickView = "waiting_approval" | "assigned_to_me" | "in_progress" | "waiting_requester" | "waiting_external" | "resolved" | "sla_breached";

export type WorkbenchTicket = {
  ticket_id: string;
  number: string | null;
  title: string;
  service: { id: string; title: string };
  category: { id: string; title: string };
  requester: { id: string; display_name: string };
  assignee: { id: string; display_name: string } | null;
  priority: ServiceDeskPriority;
  status: ServiceDeskTicketStatus;
  sla: { state: WorkbenchSlaState; metric: "first_response" | "resolution" | null; due_at: string | null };
  created_at: string;
  updated_at: string;
  allowed_actions: ServiceDeskAllowedAction[];
  active_approval_id: string | null;
};

export type WorkbenchPage = { items: WorkbenchTicket[]; page: number; page_size: number; total: number; pages: number };
export type WorkbenchCounters = Record<WorkbenchQuickView, number | null>;
export type WorkbenchUserOption = { id: string; display_name: string };
export type CatalogOption = { id: string; title: string; category_id?: string };
