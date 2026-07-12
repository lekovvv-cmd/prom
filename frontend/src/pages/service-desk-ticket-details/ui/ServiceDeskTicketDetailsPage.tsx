import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useServiceDeskAccess } from "../../../app/providers/ServiceDeskAccessProvider";
import { getServiceDeskTicket } from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import type { ServiceDeskTicket } from "../../../entities/service-desk-ticket/model/types";
import {
  ServiceDeskTicketPriorityBadge,
  ServiceDeskTicketStatusBadge
} from "../../../entities/service-desk-ticket/ui/ServiceDeskTicketBadges";
import { formatDateTime } from "../../../shared/lib/date";
import { Card } from "../../../shared/ui/Card";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";
import { Header } from "../../../widgets/header/ui/Header";
import { ServiceDeskTicketApprovals } from "../../../widgets/service-desk-ticket-approvals/ui/ServiceDeskTicketApprovals";
import { ServiceDeskTicketComments } from "../../../widgets/service-desk-ticket-comments/ui/ServiceDeskTicketComments";
import { ServiceDeskTicketActions } from "../../../widgets/service-desk-ticket-actions/ui/ServiceDeskTicketActions";
import { ServiceDeskTicketAttachments } from "../../../widgets/service-desk-ticket-attachments/ui/ServiceDeskTicketAttachments";
import { ServiceDeskTicketFieldAttachments } from "../../../widgets/service-desk-ticket-field-attachments/ui/ServiceDeskTicketFieldAttachments";

const historyLabels: Record<string, string> = {
  ticket_created: "Заявка создана",
  ticket_updated: "Заявка обновлена",
  ticket_submitted: "Заявка отправлена",
  status_changed: "Статус изменён",
  approval_requested: "Запущено согласование",
  approval_completed: "Согласование завершено",
  assigned: "Назначен исполнитель",
  reassigned: "Исполнитель изменён",
  comment_added: "Добавлен комментарий",
  attachment_uploaded: "Добавлено вложение",
  sla_breached: "Нарушен срок SLA"
};

function historyDetails(payload: Record<string, unknown>) {
  for (const key of ["comment", "reason", "resolution_summary", "file_name"]) if (typeof payload[key] === "string" && payload[key]) return String(payload[key]);
  return null;
}

function SlaSummary({ ticket }: { ticket: ServiceDeskTicket }) {
  const firstResponse = ticket.first_response_due_at ? ticket.first_response_at ? `Выполнен · ${formatDateTime(ticket.first_response_at)}` : ticket.is_response_breached ? "Срок нарушен" : `До ${formatDateTime(ticket.first_response_due_at)}` : "Не настроен";
  const resolution = ticket.resolution_due_at ? ticket.resolved_at ? `Выполнено · ${formatDateTime(ticket.resolved_at)}` : ticket.is_resolution_breached ? "Срок нарушен" : `До ${formatDateTime(ticket.resolution_due_at)}` : "Не настроено";
  const paused = ticket.paused_seconds ? `${Math.round(ticket.paused_seconds / 60)} мин` : "Нет";
  return <Card><h3>SLA</h3><dl className="side-list"><div><dt>Первый ответ</dt><dd>{firstResponse}</dd></div><div><dt>Выполнение</dt><dd>{resolution}</dd></div><div><dt>Состояние</dt><dd>{ticket.is_response_breached || ticket.is_resolution_breached ? "Срок нарушен" : ticket.status === "waiting_requester" ? "На паузе: ожидается ответ заявителя" : "В срок"}</dd></div><div><dt>Пауза</dt><dd>{paused}</dd></div></dl></Card>;
}

export function ServiceDeskTicketDetailsPage() {
  const { ticketId } = useParams();
  const { user } = useServiceDeskAccess();
  const [ticket, setTicket] = useState<ServiceDeskTicket | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadTicket = useCallback(async () => {
    if (!ticketId) {
      setError("Не указан идентификатор заявки");
      setIsLoading(false);
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      setTicket(await getServiceDeskTicket(ticketId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить заявку");
    } finally {
      setIsLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    void loadTicket();
  }, [loadTicket]);

  const fieldEntries = ticket?.field_snapshot?.length ? ticket.field_snapshot : ticket ? Object.entries(ticket.field_values).map(([key, value]) => ({ key, label: key.replaceAll("_", " "), type: "text", raw_value: value, display_value: String(value ?? "Не указано") })) : [];

  return (
    <>
      <Header />
      <PageLayout
        title={ticket?.number ?? "Заявка Service Desk"}
        subtitle={ticket ? `${ticket.service.category.title} · ${ticket.service.title}` : undefined}
      >
        <nav className="breadcrumbs" aria-label="Навигация по заявкам"><Link to="/service-desk">Каталог</Link><span>→</span><Link to="/service-desk/my-tickets">Мои заявки</Link><span>→</span><span>{ticket?.number ?? "Заявка"}</span></nav>
        {error && <p className="form-error">{error}</p>}
        {isLoading && <Spinner label="Загружаем заявку" />}
        {!isLoading && ticket && user && (
          <div className="service-desk-ticket-layout">
            <section className="service-desk-ticket-main">
              <div className="details-heading service-desk-ticket-heading">
                <div className="card-topline">
                  <ServiceDeskTicketStatusBadge status={ticket.status} />
                  <ServiceDeskTicketPriorityBadge priority={ticket.priority} />
                </div>
                <h2>{ticket.title}</h2>
                <p>{ticket.description ?? "Описание не указано."}</p>
              </div>

              <ServiceDeskTicketApprovals
                currentUserId={user.id}
                ticket={ticket}
                onTicketChanged={setTicket}
              />

              <ServiceDeskTicketActions ticket={ticket} onTicketChanged={setTicket} />

              <ServiceDeskTicketComments
                currentUser={user}
                ticket={ticket}
                onTicketChanged={loadTicket}
              />

              {fieldEntries.length > 0 && (
                <Card>
                  <h3>Поля заявки</h3>
                  <dl className="service-desk-field-list">
                    {fieldEntries.map((field) => (
                      <div key={field.label}>
                        <dt>{field.label}</dt>
                        <dd>{field.display_value}</dd>
                      </div>
                    ))}
                  </dl>
                </Card>
              )}
              {ticket ? <ServiceDeskTicketFieldAttachments ticketId={ticket.id} fields={fieldEntries.map((field) => ({ key: field.key, label: field.label, type: field.type }))} canDelete={user.access_type === "service_desk_admin" || (ticket.status === "draft" && ticket.requester_user_id === user.id)} /> : null}

              <Card>
                <h3>История</h3>
                <ol className="service-desk-history">
                  {ticket.history.map((event) => (
                    <li key={event.id}>
                      <span>{formatDateTime(event.created_at)}</span>
                      <div>
                        <strong>{historyLabels[event.event_type] ?? event.message}</strong>
                        {historyDetails(event.payload) ? <p>{historyDetails(event.payload)}</p> : null}
                      </div>
                    </li>
                  ))}
                </ol>
              </Card>
            </section>

            <aside className="service-desk-ticket-side">
              <Card>
                <span className="service-desk-eyebrow">Заявитель</span>
                <h3>{ticket.requester.display_name}</h3>
                <p className="muted">{ticket.requester.email}</p>
              </Card>
              <Card>
                <h3>Параметры</h3>
                <dl className="side-list">
                  <div>
                    <dt>Создана</dt>
                    <dd>{formatDateTime(ticket.created_at)}</dd>
                  </div>
                  <div>
                    <dt>Отправлена</dt>
                    <dd>{formatDateTime(ticket.submitted_at)}</dd>
                  </div>
                  <div>
                    <dt>Исполнитель</dt>
                    <dd>{ticket.assignee?.display_name ?? "Не назначен"}</dd>
                  </div>
                  <div>
                    <dt>Текущий пользователь</dt>
                    <dd>{user.display_name}</dd>
                  </div>
                </dl>
              </Card>
              <SlaSummary ticket={ticket} />
              <ServiceDeskTicketAttachments ticketId={ticket.id} canUpload={!['closed', 'cancelled'].includes(ticket.status)} canDelete={user.access_type === "service_desk_admin" || (ticket.status === "draft" && ticket.requester_user_id === user.id)} />
            </aside>
          </div>
        )}
      </PageLayout>
    </>
  );
}
