import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Clipboard, Plus, Search } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { getMyServiceDeskTickets } from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import type { ServiceDeskTicket } from "../../../entities/service-desk-ticket/model/types";
import { serviceDeskQueryKeys } from "../../../api/queryKeys";
import {
  ServiceDeskTicketPriorityBadge,
  ServiceDeskTicketStatusBadge,
} from "../../../entities/service-desk-ticket/ui/ServiceDeskTicketBadges";
import { formatDateTime } from "@prom/utils/date";
import { Card } from "@prom/ui/Card";
import { Input } from "@prom/ui/Input";
import { PageLayout } from "@prom/ui/PageLayout";
import { Spinner } from "@prom/ui/Spinner";
import { Header } from "@prom/layout";

type Filter =
  "all" | "draft" | "active" | "waiting_requester" | "resolved" | "closed";
const filters: Array<[Filter, string]> = [
  ["all", "Все"],
  ["draft", "Черновики"],
  ["active", "Активные"],
  ["waiting_requester", "Ожидают моего ответа"],
  ["resolved", "Выполненные"],
  ["closed", "Закрытые"],
];

export function ServiceDeskMyTicketsPage() {
  const [filter, setFilter] = useState<Filter>("all");
  const [query, setQuery] = useState("");
  const ticketsQuery = useQuery({
    queryKey: serviceDeskQueryKeys.myTickets(),
    queryFn: ({ signal }) => getMyServiceDeskTickets(undefined, signal),
  });
  const tickets = ticketsQuery.data ?? [];
  const error =
    ticketsQuery.error instanceof Error ? ticketsQuery.error.message : null;

  const visible = useMemo(
    () =>
      tickets
        .filter((ticket) => matchesFilter(ticket, filter))
        .filter(
          (ticket) =>
            !query.trim() ||
            `${ticket.number ?? ""} ${ticket.title} ${ticket.service.title}`
              .toLowerCase()
              .includes(query.trim().toLowerCase()),
        ),
    [filter, query, tickets],
  );

  return (
    <>
      <Header />
      <PageLayout
        title="Мои заявки"
        subtitle="Здесь собраны ваши черновики и отправленные заявки."
        actions={
          <Link className="button" to="/service-desk">
            <Plus size={16} aria-hidden="true" />
            Создать заявку
          </Link>
        }
      >
        <div className="service-desk-ticket-toolbar">
          <Input
            label="Поиск"
            placeholder="Номер, тема или услуга"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <div
            className="filter-pills"
            role="tablist"
            aria-label="Фильтр заявок"
          >
            {filters.map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={filter === value ? "active" : ""}
                onClick={() => setFilter(value)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
        {ticketsQuery.isLoading ? (
          <Spinner label="Загружаем заявки" />
        ) : error ? (
          <Card>
            <p className="form-error" role="alert">
              {error}
            </p>
          </Card>
        ) : visible.length ? (
          <div className="table-wrap">
            <table className="service-desk-my-tickets-table">
              <thead>
                <tr>
                  <th>Номер</th>
                  <th>Заявка</th>
                  <th>Статус</th>
                  <th>Приоритет</th>
                  <th>Исполнитель</th>
                  <th>Обновлена</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((ticket) => {
                  const href =
                    ticket.status === "draft"
                      ? `/service-desk/tickets/${ticket.id}/edit`
                      : `/service-desk/tickets/${ticket.id}`;
                  return (
                    <tr key={ticket.id}>
                      <td>
                        <Link to={href}>{ticket.number ?? "Черновик"}</Link>
                      </td>
                      <td>
                        <Link to={href}>
                          <strong>{ticket.title}</strong>
                          <small>{ticket.service.title}</small>
                        </Link>
                      </td>
                      <td>
                        <ServiceDeskTicketStatusBadge status={ticket.status} />
                      </td>
                      <td>
                        <ServiceDeskTicketPriorityBadge
                          priority={ticket.priority}
                        />
                      </td>
                      <td>{ticket.assignee?.display_name ?? "Не назначен"}</td>
                      <td>{formatDateTime(ticket.updated_at)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <Card>
            <div className="empty-state">
              <Clipboard size={24} aria-hidden="true" />
              <h3>
                {query || filter !== "all"
                  ? "Заявки не найдены"
                  : "У вас пока нет заявок"}
              </h3>
              <p>
                {query || filter !== "all"
                  ? "Измените фильтр или запрос поиска."
                  : "Создайте первую заявку через каталог услуг."}
              </p>
              <Link className="button" to="/service-desk">
                <Search size={16} aria-hidden="true" />
                Открыть каталог
              </Link>
            </div>
          </Card>
        )}
      </PageLayout>
    </>
  );
}

function matchesFilter(ticket: ServiceDeskTicket, filter: Filter) {
  if (filter === "all") return true;
  if (filter === "active")
    return !["draft", "resolved", "closed", "cancelled", "rejected"].includes(
      ticket.status,
    );
  return ticket.status === filter;
}
