import { Link } from "react-router-dom";
import type { ServiceDeskAllowedAction } from "../../../entities/service-desk-ticket/model/types";
import { ServiceDeskTicketPriorityBadge, ServiceDeskTicketStatusBadge } from "../../../entities/service-desk-ticket/ui/ServiceDeskTicketBadges";
import type { WorkbenchTicket } from "../../../entities/service-desk-workbench/model/types";
import { WorkbenchSlaIndicator } from "../../../entities/service-desk-workbench/ui/WorkbenchSlaIndicator";
import { formatDateTime } from "../../../shared/lib/date";
import { Select } from "../../../shared/ui/Select";
import { Table } from "../../../shared/ui/Table";

const actionLabels: Record<ServiceDeskAllowedAction, string> = {
  approve: "Согласовать", reject: "Отклонить", assign: "Назначить", reassign: "Переназначить",
  start: "Взять в работу", request_clarification: "Запросить уточнение", wait_external: "Ожидать внешнее действие",
  resume: "Продолжить", resolve: "Выполнить", close: "Закрыть", cancel: "Отменить"
};

export function ServiceDeskWorkbenchTable({ items, onAction }: { items: WorkbenchTicket[]; onAction: (ticket: WorkbenchTicket, action: ServiceDeskAllowedAction) => void }) {
  return <Table><table><thead><tr><th>Номер</th><th>Заявка</th><th>Заявитель</th><th>Исполнитель</th><th>Приоритет</th><th>Статус</th><th>SLA</th><th>Создана</th><th>Обновлена</th><th>Действия</th></tr></thead>
    <tbody>{items.map((ticket) => <tr key={ticket.ticket_id}>
      <td><Link to={`/service-desk/tickets/${ticket.ticket_id}`}>{ticket.number ?? "Черновик"}</Link></td>
      <td><strong>{ticket.title}</strong><span>{ticket.service.title}</span></td>
      <td>{ticket.requester.display_name}</td><td>{ticket.assignee?.display_name ?? "—"}</td>
      <td><ServiceDeskTicketPriorityBadge priority={ticket.priority} /></td><td><ServiceDeskTicketStatusBadge status={ticket.status} /></td>
      <td data-testid="sla-cell"><WorkbenchSlaIndicator sla={ticket.sla} /></td><td>{formatDateTime(ticket.created_at)}</td><td>{formatDateTime(ticket.updated_at)}</td>
      <td>{ticket.allowed_actions.length ? <Select aria-label={`Действия ${ticket.number ?? ticket.title}`} value="" onChange={(event) => { const action = event.target.value as ServiceDeskAllowedAction; if (action) onAction(ticket, action); }}><option value="">Выберите</option>{ticket.allowed_actions.map((action) => <option key={action} value={action}>{actionLabels[action]}</option>)}</Select> : "—"}</td>
    </tr>)}</tbody></table></Table>;
}
