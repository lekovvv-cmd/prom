import { useEffect, useMemo, useState } from "react";

import { getBacklog, getSlaMetrics, getStatsDistribution, getStatsSummary, getTimeMetrics } from "../../../entities/service-desk-stats/api/serviceDeskStatsApi";
import type { BacklogBucket, DistributionItem, SlaMetrics, Summary, TimeMetrics } from "../../../entities/service-desk-stats/model/types";
import { formatDuration } from "../../../entities/service-desk-stats/lib/formatDuration";
import { Header } from "../../../widgets/header/ui/Header";
import { Card } from "../../../shared/ui/Card";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";

const cards: [keyof Summary, string][] = [
  ["created", "Всего создано"], ["closed_in_period", "Закрыто за период"], ["current_backlog", "Текущий backlog"],
  ["submitted", "Новые"], ["pending_approval", "На согласовании"], ["approved_in_period", "Согласовано"],
  ["rejected_in_period", "Отклонено"], ["assigned", "Назначено"], ["in_progress", "В работе"],
  ["waiting_requester", "Ожидают заявителя"], ["waiting_external", "Ожидают внешнего действия"],
  ["resolved", "Выполнено"], ["closed", "Закрыто"], ["cancelled_in_period", "Отменено"]
];

function Distribution({ title, items }: { title: string; items: DistributionItem[] }) {
  const max = Math.max(1, ...items.map((item) => item.count));
  return <Card><h2>{title}</h2>{items.length ? <div className="stats-bars">{items.map((item) => <div className="stats-bar" key={item.id}><span>{item.label}</span><div><i style={{ width: `${item.count / max * 100}%` }} /></div><strong>{item.count}</strong></div>)}</div> : <EmptyState title="Нет данных" />}</Card>;
}

const timeLabels: [keyof TimeMetrics, string][] = [["time_to_approval","До согласования"],["time_to_assignment","До назначения"],["first_response_time","Первый ответ"],["resolution_time","До выполнения"],["close_after_resolution_time","Закрытие после выполнения"]];
function OperationalAnalytics({ times, sla, backlog }: { times: TimeMetrics; sla: SlaMetrics; backlog: BacklogBucket[] }) {
  return <><Card><h2>Время обработки</h2><div className="table-wrap"><table><thead><tr><th>Метрика</th><th>Среднее</th><th>Медиана</th><th>P90</th><th>Выборка</th></tr></thead><tbody>{timeLabels.map(([key,label]) => { const value=times[key]; return <tr key={key}><td>{label}</td><td>{formatDuration(value.average_seconds)}</td><td>{formatDuration(value.median_seconds)}</td><td>{formatDuration(value.p90_seconds)}</td><td>{value.sample_size}</td></tr>; })}</tbody></table></div></Card>
  <div className="metric-grid"><Card><span className="muted">Response SLA</span><strong className="metric-value">{sla.response_compliance_percent === null ? "Нет данных" : `${sla.response_compliance_percent}%`}</strong></Card><Card><span className="muted">Resolution SLA</span><strong className="metric-value">{sla.resolution_compliance_percent === null ? "Нет данных" : `${sla.resolution_compliance_percent}%`}</strong></Card><Card><span className="muted">Нарушения ответа / решения</span><strong className="metric-value">{sla.response_breaches} / {sla.resolution_breaches}</strong></Card><Card><span className="muted">Рядом с нарушением / нарушены</span><strong className="metric-value">{sla.active_near_breach} / {sla.active_breached}</strong></Card></div>
  <Distribution title="Возраст backlog" items={backlog.map((item) => ({id:item.code,label:item.label,count:item.count}))} /></>;
}

export function ServiceDeskAdminDashboardPage() {
  const [dateFrom, setDateFrom] = useState(""); const [dateTo, setDateTo] = useState("");
  const [data, setData] = useState<{summary: Summary; statuses: DistributionItem[]; services: DistributionItem[]; categories: DistributionItem[]; times: TimeMetrics; sla: SlaMetrics; backlog: BacklogBucket[]} | null>(null);
  const [error, setError] = useState<string | null>(null); const [loading, setLoading] = useState(true);
  const params = useMemo(() => { const value = new URLSearchParams(); if (dateFrom) value.set("date_from", dateFrom); if (dateTo) value.set("date_to", dateTo); return value; }, [dateFrom, dateTo]);
  useEffect(() => { let active = true; setLoading(true); setError(null); Promise.all([getStatsSummary(params), getStatsDistribution("statuses", params), getStatsDistribution("services", params), getStatsDistribution("categories", params), getTimeMetrics(params), getSlaMetrics(params), getBacklog(params)]).then(([summary,statuses,services,categories,times,sla,backlog]) => active && setData({summary,statuses,services,categories,times,sla,backlog})).catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : "Не удалось загрузить аналитику")).finally(() => active && setLoading(false)); return () => { active = false; }; }, [params]);
  return <><Header /><PageLayout title="Service Desk — обзор" subtitle="Период событий считается по UTC; backlog отражает текущее состояние.">
    <Card><div className="filter-grid"><Input label="Дата с" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} /><Input label="Дата по" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} /></div></Card>
    {loading ? <Spinner label="Загружаем аналитику" /> : error ? <Card><p className="error-text">{error}</p></Card> : data ? <>
      <div className="metric-grid">{cards.map(([key,label]) => <Card key={key}><span className="muted">{label}</span><strong className="metric-value">{data.summary[key] as number}</strong></Card>)}</div>
      <div className="dashboard-grid"><Distribution title="По статусам" items={data.statuses} /><Distribution title="По приоритетам" items={data.summary.priorities} /><Distribution title="По категориям" items={data.categories} /><Distribution title="По услугам" items={data.services} /></div>
      <OperationalAnalytics times={data.times} sla={data.sla} backlog={data.backlog} />
    </> : null}
  </PageLayout></>;
}
