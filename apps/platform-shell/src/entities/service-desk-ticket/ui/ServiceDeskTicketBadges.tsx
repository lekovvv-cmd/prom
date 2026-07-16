import type {
  ServiceDeskPriority,
  ServiceDeskTicketStatus
} from "../model/types";
import { Badge } from "../../../shared/ui/Badge";

const statusMeta: Record<ServiceDeskTicketStatus, { label: string; tone: string }> = {
  draft: { label: "Черновик", tone: "muted" },
  submitted: { label: "Зарегистрирована", tone: "info" },
  pending_approval: { label: "На согласовании", tone: "warning" },
  approved: { label: "Согласована", tone: "success" },
  rejected: { label: "Отклонена", tone: "danger" },
  assigned: { label: "Назначена", tone: "info" },
  in_progress: { label: "В работе", tone: "info" },
  waiting_requester: { label: "Ожидает заявителя", tone: "warning" },
  waiting_external: { label: "Внешнее ожидание", tone: "warning" },
  resolved: { label: "Выполнена", tone: "success" },
  closed: { label: "Закрыта", tone: "muted" },
  cancelled: { label: "Отменена", tone: "muted" }
};

const priorityMeta: Record<ServiceDeskPriority, { label: string; tone: string }> = {
  low: { label: "Низкий приоритет", tone: "muted" },
  medium: { label: "Средний приоритет", tone: "neutral" },
  high: { label: "Высокий приоритет", tone: "warning" },
  critical: { label: "Критический приоритет", tone: "danger" }
};

export function ServiceDeskTicketStatusBadge({ status }: { status: ServiceDeskTicketStatus }) {
  const meta = statusMeta[status];
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}

export function ServiceDeskTicketPriorityBadge({ priority }: { priority: ServiceDeskPriority }) {
  const meta = priorityMeta[priority];
  return <Badge tone={meta.tone}>{meta.label}</Badge>;
}
