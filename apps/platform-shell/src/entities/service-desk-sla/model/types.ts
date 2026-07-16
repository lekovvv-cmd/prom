export type BusinessHours = { weekday: number; start_time: string; end_time: string };
export type CalendarException = { date: string; type: "holiday" | "working_day" | "custom_hours"; start_time?: string; end_time?: string; description?: string };
export type BusinessCalendar = { id: string; name: string; timezone: string; is_active: boolean; business_hours: BusinessHours[]; exceptions: CalendarException[] };
export type SlaPolicy = { id: string; name: string; description?: string; is_active: boolean; business_calendar_id: string; first_response_minutes: number; resolution_minutes: number; pause_statuses: Array<"waiting_requester" | "waiting_external"> };
export type SlaBindingConditionField = "template_version_id" | "service_id" | "category_id" | "priority" | "field_value";
export type SlaBindingCondition = { field: SlaBindingConditionField; value: string; field_key?: string | null };
export type SlaBinding = { id: string; policy_id: string; name: string; priority: number; is_active: boolean; conditions: SlaBindingCondition[] };
export type EscalationMetric = "first_response" | "resolution";
export type EscalationActionType = "create_in_app_notification" | "email_notification_when_available";
export type EscalationRecipientType = "assignee" | "requester" | "service_desk_admin" | "specific_user";
export type EscalationRule = { id: string; sla_policy_id: string; metric: EscalationMetric; threshold_percent: number; action_type: EscalationActionType; recipient_type: EscalationRecipientType; recipient_user_id?: string | null; is_active: boolean };
export type SlaRecipient = { id: string; display_name: string; email: string };

export type BusinessCalendarPayload = Omit<BusinessCalendar, "id">;
export type SlaPolicyPayload = Omit<SlaPolicy, "id">;
export type SlaBindingPayload = Omit<SlaBinding, "id">;
export type EscalationRulePayload = Omit<EscalationRule, "id" | "sla_policy_id">;
