import type {
  BusinessCalendar,
  BusinessCalendarPayload,
  BusinessHours,
  CalendarException,
  EscalationActionType,
  EscalationMetric,
  EscalationRecipientType,
  EscalationRule,
  EscalationRulePayload,
  SlaBinding,
  SlaBindingCondition,
  SlaBindingConditionField,
  SlaBindingPayload,
  SlaPolicy,
  SlaPolicyPayload,
} from "../../../entities/service-desk-sla/model/types";

export type CalendarDraft = {
  name: string;
  timezone: string;
  isActive: boolean;
  businessHours: BusinessHours[];
  exceptions: CalendarException[];
};

export type PolicyDraft = {
  name: string;
  description: string;
  isActive: boolean;
  calendarId: string;
  firstResponseMinutes: string;
  resolutionMinutes: string;
  pauseStatuses: SlaPolicy["pause_statuses"];
};

export type BindingDraft = {
  name: string;
  policyId: string;
  priority: string;
  isActive: boolean;
  conditions: SlaBindingCondition[];
};

export type EscalationDraft = {
  policyId: string;
  metric: EscalationMetric;
  thresholdPercent: string;
  actionType: EscalationActionType;
  recipientType: EscalationRecipientType;
  recipientUserId: string;
  isActive: boolean;
};

export const WEEKDAY_OPTIONS = [
  { value: 0, label: "Понедельник" },
  { value: 1, label: "Вторник" },
  { value: 2, label: "Среда" },
  { value: 3, label: "Четверг" },
  { value: 4, label: "Пятница" },
  { value: 5, label: "Суббота" },
  { value: 6, label: "Воскресенье" },
];

export const BINDING_FIELD_OPTIONS: Array<{
  value: SlaBindingConditionField;
  label: string;
}> = [
  { value: "template_version_id", label: "Версия шаблона" },
  { value: "service_id", label: "Услуга" },
  { value: "category_id", label: "Категория" },
  { value: "priority", label: "Приоритет заявки" },
  { value: "field_value", label: "Значение поля формы" },
];

export function emptyBusinessHours(): BusinessHours {
  return { weekday: 0, start_time: "09:00", end_time: "18:00" };
}

export function emptyCalendarException(): CalendarException {
  return { date: "", type: "holiday", description: "" };
}

export function emptyBindingCondition(): SlaBindingCondition {
  return { field: "service_id", value: "" };
}

export function emptyCalendarDraft(): CalendarDraft {
  return {
    name: "",
    timezone: "Asia/Yekaterinburg",
    isActive: true,
    businessHours: [emptyBusinessHours()],
    exceptions: [],
  };
}

export function calendarToDraft(calendar: BusinessCalendar): CalendarDraft {
  return {
    name: calendar.name,
    timezone: calendar.timezone,
    isActive: calendar.is_active,
    businessHours: calendar.business_hours.map(
      ({ weekday, start_time, end_time }) => ({
        weekday,
        start_time: start_time.slice(0, 5),
        end_time: end_time.slice(0, 5),
      }),
    ),
    exceptions: calendar.exceptions.map(
      ({ date, type, start_time, end_time, description }) => ({
        date,
        type,
        start_time: start_time?.slice(0, 5),
        end_time: end_time?.slice(0, 5),
        description: description ?? "",
      }),
    ),
  };
}

export function calendarDraftToPayload(
  draft: CalendarDraft,
): BusinessCalendarPayload {
  return {
    name: draft.name.trim(),
    timezone: draft.timezone.trim(),
    is_active: draft.isActive,
    business_hours: draft.businessHours.map((interval) => ({
      weekday: interval.weekday,
      start_time: interval.start_time,
      end_time: interval.end_time,
    })),
    exceptions: draft.exceptions.map((exception) => ({
      date: exception.date,
      type: exception.type,
      description: exception.description?.trim() || undefined,
      ...(exception.type === "custom_hours"
        ? { start_time: exception.start_time, end_time: exception.end_time }
        : {}),
    })),
  };
}

export function emptyPolicyDraft(calendarId = ""): PolicyDraft {
  return {
    name: "",
    description: "",
    isActive: true,
    calendarId,
    firstResponseMinutes: "30",
    resolutionMinutes: "240",
    pauseStatuses: [],
  };
}

export function policyToDraft(policy: SlaPolicy): PolicyDraft {
  return {
    name: policy.name,
    description: policy.description ?? "",
    isActive: policy.is_active,
    calendarId: policy.business_calendar_id,
    firstResponseMinutes: String(policy.first_response_minutes),
    resolutionMinutes: String(policy.resolution_minutes),
    pauseStatuses: [...policy.pause_statuses],
  };
}

export function policyDraftToPayload(draft: PolicyDraft): SlaPolicyPayload {
  return {
    name: draft.name.trim(),
    description: draft.description.trim() || undefined,
    is_active: draft.isActive,
    business_calendar_id: draft.calendarId,
    first_response_minutes: Number(draft.firstResponseMinutes),
    resolution_minutes: Number(draft.resolutionMinutes),
    pause_statuses: draft.pauseStatuses,
  };
}

export function emptyBindingDraft(policyId = ""): BindingDraft {
  return {
    name: "",
    policyId,
    priority: "100",
    isActive: true,
    conditions: [emptyBindingCondition()],
  };
}

export function bindingToDraft(binding: SlaBinding): BindingDraft {
  return {
    name: binding.name,
    policyId: binding.policy_id,
    priority: String(binding.priority),
    isActive: binding.is_active,
    conditions: binding.conditions.map((condition) => ({ ...condition })),
  };
}

export function bindingDraftToPayload(draft: BindingDraft): SlaBindingPayload {
  return {
    name: draft.name.trim(),
    policy_id: draft.policyId,
    priority: Number(draft.priority),
    is_active: draft.isActive,
    conditions: draft.conditions.map((condition) => ({
      field: condition.field,
      value: condition.value.trim(),
      field_key:
        condition.field === "field_value"
          ? condition.field_key?.trim()
          : undefined,
    })),
  };
}

export function emptyEscalationDraft(policyId = ""): EscalationDraft {
  return {
    policyId,
    metric: "resolution",
    thresholdPercent: "80",
    actionType: "create_in_app_notification",
    recipientType: "assignee",
    recipientUserId: "",
    isActive: true,
  };
}

export function escalationToDraft(rule: EscalationRule): EscalationDraft {
  return {
    policyId: rule.sla_policy_id,
    metric: rule.metric,
    thresholdPercent: String(rule.threshold_percent),
    actionType: rule.action_type,
    recipientType: rule.recipient_type,
    recipientUserId: rule.recipient_user_id ?? "",
    isActive: rule.is_active,
  };
}

export function escalationDraftToPayload(
  draft: EscalationDraft,
): EscalationRulePayload {
  return {
    metric: draft.metric,
    threshold_percent: Number(draft.thresholdPercent),
    action_type: draft.actionType,
    recipient_type: draft.recipientType,
    recipient_user_id:
      draft.recipientType === "specific_user" ? draft.recipientUserId : null,
    is_active: draft.isActive,
  };
}
