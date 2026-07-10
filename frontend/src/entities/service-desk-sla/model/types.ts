export type BusinessHours = { weekday: number; start_time: string; end_time: string };
export type CalendarException = { date: string; type: "holiday" | "working_day" | "custom_hours"; start_time?: string; end_time?: string; description?: string };
export type BusinessCalendar = { id: string; name: string; timezone: string; is_active: boolean; business_hours: BusinessHours[]; exceptions: CalendarException[] };
export type SlaPolicy = { id: string; name: string; description?: string; is_active: boolean; business_calendar_id: string; first_response_minutes: number; resolution_minutes: number; pause_statuses: Array<"waiting_requester" | "waiting_external"> };
export type SlaBinding = { id: string; policy_id: string; name: string; priority: number; is_active: boolean; conditions: Array<{ field: string; value: string; field_key?: string }> };
export type EscalationRule = { id: string; sla_policy_id: string; metric: "first_response" | "resolution"; threshold_percent: number; action_type: string; recipient_type: string; recipient_user_id?: string; is_active: boolean };
