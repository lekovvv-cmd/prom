import { useEffect, useMemo, useState } from "react";

import { formatDuration } from "../../../entities/service-desk-stats/lib/formatDuration";
import type {
  ApprovalMetrics,
  AssigneeStats,
  BacklogBucket,
  DistributionItem,
  SlaMetrics,
  Summary,
  TimeMetrics
} from "../../../entities/service-desk-stats/model/types";
import {
  getApprovalMetrics,
  getAssignees,
  getBacklog,
  getSlaMetrics,
  getStatsDistribution,
  getStatsSummary,
  getTimeMetrics
} from "../../../entities/service-desk-stats/api/serviceDeskStatsApi";
import {
  getWorkbenchCategories,
  getWorkbenchServices
} from "../../../entities/service-desk-workbench/api/serviceDeskWorkbenchApi";
import type { CatalogOption } from "../../../entities/service-desk-workbench/model/types";
import { Header } from "../../../widgets/header/ui/Header";
import { ServiceDeskAdminNav } from "../../../widgets/service-desk-admin-nav/ui/ServiceDeskAdminNav";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";

export type StatsFilterState = {
  dateFrom: string;
  dateTo: string;
  categoryId: string;
  serviceId: string;
  assigneeUserId: string;
  priority: string;
};

export const emptyStatsFilters: StatsFilterState = {
  dateFrom: "",
  dateTo: "",
  categoryId: "",
  serviceId: "",
  assigneeUserId: "",
  priority: ""
};

export function buildStatsParams(filters: StatsFilterState) {
  const params = new URLSearchParams();
  if (filters.dateFrom) params.set("date_from", filters.dateFrom);
  if (filters.dateTo) params.set("date_to", filters.dateTo);
  if (filters.categoryId) params.set("category_id", filters.categoryId);
  if (filters.serviceId) params.set("service_id", filters.serviceId);
  if (filters.assigneeUserId) params.set("assignee_user_id", filters.assigneeUserId);
  if (filters.priority) params.set("priority", filters.priority);
  return params;
}

const summaryCards: Array<[keyof Summary, string]> = [
  ["created", "Всего создано"],
  ["closed_in_period", "Закрыто за период"],
  ["current_backlog", "Текущий backlog"],
  ["submitted", "Новые"],
  ["pending_approval", "На согласовании"],
  ["approved_in_period", "Согласовано"],
  ["rejected_in_period", "Отклонено"],
  ["assigned", "Назначено"],
  ["in_progress", "В работе"],
  ["waiting_requester", "Ожидают заявителя"],
  ["waiting_external", "Ожидают внешнего действия"],
  ["resolved", "Выполнено"],
  ["closed", "Закрыто"],
  ["cancelled_in_period", "Отменено"]
];

const timeLabels: Array<[keyof TimeMetrics, string]> = [
  ["time_to_approval", "До согласования"],
  ["time_to_assignment", "До назначения"],
  ["first_response_time", "Первый ответ"],
  ["resolution_time", "До выполнения"],
  ["close_after_resolution_time", "Закрытие после выполнения"]
];

type DashboardData = {
  summary: Summary;
  statuses: DistributionItem[];
  services: DistributionItem[];
  categories: DistributionItem[];
  times: TimeMetrics;
  sla: SlaMetrics;
  backlog: BacklogBucket[];
  assignees: AssigneeStats[];
  approvals: ApprovalMetrics;
};

function Distribution({ title, items }: { title: string; items: DistributionItem[] }) {
  const max = Math.max(1, ...items.map((item) => item.count));
  if (!items.length) {
    return <Card><h2>{title}</h2><EmptyState title="Нет данных" /></Card>;
  }
  return (
    <Card>
      <h2>{title}</h2>
      <div className="stats-bars">
        {items.map((item) => (
          <div className="stats-bar" key={item.id}>
            <span>{item.label}</span>
            <div><i style={{ width: `${(item.count / max) * 100}%` }} /></div>
            <strong>{item.count}</strong>
          </div>
        ))}
      </div>
    </Card>
  );
}

function OperationalAnalytics({
  times,
  sla,
  backlog
}: {
  times: TimeMetrics;
  sla: SlaMetrics;
  backlog: BacklogBucket[];
}) {
  return (
    <>
      <Card>
        <h2>Время обработки</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Метрика</th><th>Среднее</th><th>Медиана</th><th>P90</th><th>Выборка</th></tr>
            </thead>
            <tbody>
              {timeLabels.map(([key, label]) => {
                const value = times[key];
                return (
                  <tr key={key}>
                    <td>{label}</td>
                    <td>{formatDuration(value.average_seconds)}</td>
                    <td>{formatDuration(value.median_seconds)}</td>
                    <td>{formatDuration(value.p90_seconds)}</td>
                    <td>{value.sample_size}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
      <div className="metric-grid">
        <Card><span className="muted">Response SLA</span><strong className="metric-value">{sla.response_compliance_percent === null ? "Нет данных" : `${sla.response_compliance_percent}%`}</strong></Card>
        <Card><span className="muted">Resolution SLA</span><strong className="metric-value">{sla.resolution_compliance_percent === null ? "Нет данных" : `${sla.resolution_compliance_percent}%`}</strong></Card>
        <Card><span className="muted">Нарушения ответа / решения</span><strong className="metric-value">{sla.response_breaches} / {sla.resolution_breaches}</strong></Card>
        <Card><span className="muted">Рядом с нарушением / нарушены</span><strong className="metric-value">{sla.active_near_breach} / {sla.active_breached}</strong></Card>
      </div>
      <Distribution
        title="Возраст backlog"
        items={backlog.map((item) => ({ id: item.code, label: item.label, count: item.count }))}
      />
    </>
  );
}

function PeopleAnalytics({
  assignees,
  approvals
}: {
  assignees: AssigneeStats[];
  approvals: ApprovalMetrics;
}) {
  const duration = approvals.stage_duration;
  return (
    <>
      <Card>
        <h2>Исполнители</h2>
        {assignees.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Исполнитель</th><th>Назначено</th><th>В работе</th><th>Waiting</th>
                  <th>Resolved</th><th>Closed</th><th>SLA breaches</th><th>Медиана решения</th>
                </tr>
              </thead>
              <tbody>
                {assignees.map((row) => (
                  <tr key={row.user_id}>
                    <td>{row.display_name}{!row.is_active && <small className="muted"> · доступ отключен</small>}</td>
                    <td>{row.currently_assigned}</td>
                    <td>{row.in_progress}</td>
                    <td>{row.waiting}</td>
                    <td>{row.resolved_in_period}</td>
                    <td>{row.closed_in_period}</td>
                    <td>{row.breached_tickets}</td>
                    <td>{formatDuration(row.median_resolution_seconds)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : <EmptyState title="Нет данных по исполнителям" />}
      </Card>
      <Card>
        <h2>Согласования</h2>
        <div className="metric-grid">
          <div><span>Ожидают решения</span><strong className="metric-value">{approvals.pending_approval_stages}</strong></div>
          <div><span>Среднее</span><strong>{formatDuration(duration.average_seconds)}</strong></div>
          <div><span>Медиана</span><strong>{formatDuration(duration.median_seconds)}</strong></div>
          <div><span>P90</span><strong>{formatDuration(duration.p90_seconds)}</strong></div>
          <div><span>Доля отклонений</span><strong>{approvals.rejection_rate_percent === null ? "Нет данных" : `${approvals.rejection_rate_percent}%`}</strong></div>
        </div>
      </Card>
    </>
  );
}

export function ServiceDeskAdminDashboardPage() {
  const [filters, setFilters] = useState<StatsFilterState>(emptyStatsFilters);
  const [categories, setCategories] = useState<CatalogOption[]>([]);
  const [services, setServices] = useState<CatalogOption[]>([]);
  const [assigneeOptions, setAssigneeOptions] = useState<AssigneeStats[]>([]);
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const params = useMemo(() => buildStatsParams(filters), [filters]);

  useEffect(() => {
    void Promise.all([
      getWorkbenchCategories(),
      getWorkbenchServices(),
      getAssignees(new URLSearchParams())
    ]).then(([categoryItems, serviceItems, assigneeItems]) => {
      setCategories(categoryItems);
      setServices(serviceItems);
      setAssigneeOptions(assigneeItems);
    }).catch(() => undefined);
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    Promise.all([
      getStatsSummary(params),
      getStatsDistribution("statuses", params),
      getStatsDistribution("services", params),
      getStatsDistribution("categories", params),
      getTimeMetrics(params),
      getSlaMetrics(params),
      getBacklog(params),
      getAssignees(params),
      getApprovalMetrics(params)
    ])
      .then(([summary, statuses, serviceItems, categoryItems, times, sla, backlog, assignees, approvals]) => {
        if (active) setData({ summary, statuses, services: serviceItems, categories: categoryItems, times, sla, backlog, assignees, approvals });
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Не удалось загрузить аналитику");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [params]);

  function updateFilter(key: keyof StatsFilterState, value: string) {
    setFilters((current) => ({
      ...current,
      [key]: value,
      ...(key === "categoryId" ? { serviceId: "" } : {})
    }));
  }

  return (
    <>
      <Header />
      <ServiceDeskAdminNav />
      <PageLayout title="Service Desk - обзор" subtitle="Период событий считается по UTC; backlog отражает текущее состояние.">
        <Card>
          <div className="filter-grid">
            <Input label="Дата с" type="date" value={filters.dateFrom} onChange={(event) => updateFilter("dateFrom", event.target.value)} />
            <Input label="Дата по" type="date" value={filters.dateTo} onChange={(event) => updateFilter("dateTo", event.target.value)} />
            <Select label="Категория" value={filters.categoryId} onChange={(event) => updateFilter("categoryId", event.target.value)}>
              <option value="">Все</option>
              {categories.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
            </Select>
            <Select label="Услуга" value={filters.serviceId} onChange={(event) => updateFilter("serviceId", event.target.value)}>
              <option value="">Все</option>
              {services.filter((item) => !filters.categoryId || item.category_id === filters.categoryId).map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}
            </Select>
            <Select label="Исполнитель" value={filters.assigneeUserId} onChange={(event) => updateFilter("assigneeUserId", event.target.value)}>
              <option value="">Все</option>
              {assigneeOptions.map((item) => <option key={item.user_id} value={item.user_id}>{item.display_name}</option>)}
            </Select>
            <Select label="Приоритет" value={filters.priority} onChange={(event) => updateFilter("priority", event.target.value)}>
              <option value="">Все</option><option value="low">Низкий</option><option value="medium">Средний</option><option value="high">Высокий</option><option value="critical">Критический</option>
            </Select>
            <Button variant="ghost" onClick={() => setFilters(emptyStatsFilters)}>Сбросить</Button>
          </div>
        </Card>

        {loading ? <Spinner label="Загружаем аналитику" /> : error ? <Card><p className="error-text">{error}</p></Card> : data ? (
          <>
            <div className="metric-grid">
              {summaryCards.map(([key, label]) => (
                <Card key={key}><span className="muted">{label}</span><strong className="metric-value">{data.summary[key] as number}</strong></Card>
              ))}
            </div>
            <div className="dashboard-grid">
              <Distribution title="По статусам" items={data.statuses} />
              <Distribution title="По приоритетам" items={data.summary.priorities} />
              <Distribution title="По категориям" items={data.categories} />
              <Distribution title="По услугам" items={data.services} />
            </div>
            <OperationalAnalytics times={data.times} sla={data.sla} backlog={data.backlog} />
            <PeopleAnalytics assignees={data.assignees} approvals={data.approvals} />
          </>
        ) : null}
      </PageLayout>
    </>
  );
}
