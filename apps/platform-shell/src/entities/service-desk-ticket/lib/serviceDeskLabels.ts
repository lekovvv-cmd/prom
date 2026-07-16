import type { ServiceDeskAllowedAction, ServiceDeskPriority, ServiceDeskTicketStatus } from "../model/types";

export const serviceDeskStatusLabels: Record<ServiceDeskTicketStatus, string> = {
  draft: "Черновик",
  submitted: "Зарегистрирована",
  pending_approval: "На согласовании",
  approved: "Согласована",
  rejected: "Отклонена",
  assigned: "Назначена",
  in_progress: "В работе",
  waiting_requester: "Ожидает заявителя",
  waiting_external: "Внешнее ожидание",
  resolved: "Выполнена",
  closed: "Закрыта",
  cancelled: "Отменена"
};

export const serviceDeskPriorityLabels: Record<ServiceDeskPriority, string> = {
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
  critical: "Критический"
};

export const serviceDeskActionLabels: Record<ServiceDeskAllowedAction, string> = {
  approve: "Согласовать",
  reject: "Отклонить",
  assign: "Назначить",
  reassign: "Переназначить",
  start: "Взять в работу",
  request_clarification: "Запросить уточнение",
  wait_external: "Передать во внешнее ожидание",
  resume: "Возобновить",
  resolve: "Отметить выполненной",
  close: "Закрыть",
  cancel: "Отменить",
  change_priority: "Изменить приоритет"
};

export const serviceDeskSlaLabels = {
  first_response: "Первый ответ",
  resolution: "Выполнение",
  on_track: "В срок",
  paused: "На паузе",
  warning: "Приближается срок",
  breached: "Срок нарушен",
  no_sla: "SLA не настроен"
} as const;

export function getServiceDeskActionLabel(action: string) {
  return serviceDeskActionLabels[action as ServiceDeskAllowedAction] ?? "Действие";
}
