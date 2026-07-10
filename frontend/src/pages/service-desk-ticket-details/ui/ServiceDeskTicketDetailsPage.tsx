import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

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

function formatFieldValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "Не указано";
  }
  if (typeof value === "boolean") {
    return value ? "Да" : "Нет";
  }
  if (Array.isArray(value)) {
    return value.map(formatFieldValue).join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

function formatFieldKey(key: string) {
  return key.replaceAll("_", " ");
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

  const fieldEntries = ticket ? Object.entries(ticket.field_values) : [];

  return (
    <>
      <Header />
      <PageLayout
        title={ticket?.number ?? "Заявка Service Desk"}
        subtitle={ticket ? `${ticket.service.category.title} · ${ticket.service.title}` : undefined}
      >
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

              <ServiceDeskTicketComments
                currentUser={user}
                ticket={ticket}
                onTicketChanged={loadTicket}
              />

              {fieldEntries.length > 0 && (
                <Card>
                  <h3>Поля заявки</h3>
                  <dl className="service-desk-field-list">
                    {fieldEntries.map(([key, value]) => (
                      <div key={key}>
                        <dt>{formatFieldKey(key)}</dt>
                        <dd>{formatFieldValue(value)}</dd>
                      </div>
                    ))}
                  </dl>
                </Card>
              )}

              <Card>
                <h3>История</h3>
                <ol className="service-desk-history">
                  {ticket.history.map((event) => (
                    <li key={event.id}>
                      <span>{formatDateTime(event.created_at)}</span>
                      <div>
                        <strong>{event.message}</strong>
                        {typeof event.payload.comment === "string" && event.payload.comment && (
                          <p>{event.payload.comment}</p>
                        )}
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
            </aside>
          </div>
        )}
      </PageLayout>
    </>
  );
}
