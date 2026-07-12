import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { getWorkbenchCategories, getWorkbenchCounters, getWorkbenchServices, getWorkbenchTickets, getWorkbenchUsers, performWorkbenchAction } from "../../../entities/service-desk-workbench/api/serviceDeskWorkbenchApi";
import type { CatalogOption, WorkbenchCounters, WorkbenchQuickView, WorkbenchTicket, WorkbenchUserOption } from "../../../entities/service-desk-workbench/model/types";
import type { ServiceDeskAllowedAction } from "../../../entities/service-desk-ticket/model/types";
import { ServiceDeskWorkbenchTable } from "../../../widgets/service-desk-workbench-table/ui/ServiceDeskWorkbenchTable";
import { subscribeToServiceDeskRefresh } from "../../../shared/lib/serviceDeskRefresh";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Input } from "../../../shared/ui/Input";
import { Modal } from "../../../shared/ui/Modal";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";
import {
  buildWorkbenchParams,
  initialWorkbenchFilters,
  shouldShowInitialWorkbenchSpinner,
  updateWorkbenchFilter,
  updateWorkbenchPage
} from "../model/workbenchFilters";

export const workbenchStatusOptions = [
  ["", "Все статусы"],
  ["submitted", "Зарегистрирована"],
  ["pending_approval", "На согласовании"],
  ["approved", "Согласована"],
  ["rejected", "Отклонена"],
  ["assigned", "Назначена"],
  ["in_progress", "В работе"],
  ["waiting_requester", "Ожидает заявителя"],
  ["waiting_external", "Внешнее ожидание"],
  ["resolved", "Выполнена"],
  ["closed", "Закрыта"],
  ["cancelled", "Отменена"]
];

const quickLabels: Record<WorkbenchQuickView, string> = {
  waiting_approval: "На согласование",
  assigned_to_me: "Назначены мне",
  in_progress: "В работе",
  waiting_requester: "Ожидают заявителя",
  waiting_external: "Ожидают внешнего действия",
  resolved: "Выполнены",
  sla_breached: "Нарушение SLA"
};

const payloadFields: Partial<Record<ServiceDeskAllowedAction, [string, string]>> = {
  reject: ["comment", "Причина отклонения"],
  request_clarification: ["comment", "Комментарий заявителю"],
  wait_external: ["reason", "Причина ожидания"],
  resolve: ["resolution_summary", "Результат решения"],
  cancel: ["reason", "Причина отмены"]
};

type WorkbenchPageData = { items: WorkbenchTicket[]; total: number; pages: number };

export function ServiceDeskWorkbenchPage() {
  const [filters, setFilters] = useState(initialWorkbenchFilters);
  const [search, setSearch] = useState("");
  const [data, setData] = useState<WorkbenchPageData | null>(null);
  const [counters, setCounters] = useState<WorkbenchCounters | null>(null);
  const [users, setUsers] = useState<WorkbenchUserOption[]>([]);
  const [assignees, setAssignees] = useState<WorkbenchUserOption[]>([]);
  const [categories, setCategories] = useState<CatalogOption[]>([]);
  const [services, setServices] = useState<CatalogOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<{ ticket: WorkbenchTicket; action: ServiceDeskAllowedAction } | null>(null);
  const [payload, setPayload] = useState("");
  const [pending, setPending] = useState(false);
  const requestSeq = useRef(0);
  const hasDataRef = useRef(false);

  const params = useMemo(() => buildWorkbenchParams(filters, search), [filters, search]);

  const load = useCallback(async ({ silent = false }: { silent?: boolean } = {}) => {
    const seq = requestSeq.current + 1;
    requestSeq.current = seq;
    if (!silent || !hasDataRef.current) setLoading(true);
    if (!silent) setError(null);
    try {
      const [page, counts] = await Promise.all([getWorkbenchTickets(params), getWorkbenchCounters()]);
      if (requestSeq.current !== seq) return;
      hasDataRef.current = true;
      setData(page);
      setCounters(counts);
      setError(null);
    } catch (reason) {
      if (requestSeq.current !== seq) return;
      setError(reason instanceof Error ? reason.message : "Не удалось загрузить рабочее место");
    } finally {
      if (requestSeq.current === seq) setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load({ silent: false }), 300);
    return () => window.clearTimeout(timer);
  }, [load]);

  useEffect(() => subscribeToServiceDeskRefresh(() => void load({ silent: true })), [load]);

  useEffect(() => {
    void Promise.all([
      getWorkbenchUsers(),
      getWorkbenchUsers(true),
      getWorkbenchCategories(),
      getWorkbenchServices()
    ]).then(([allUsers, eligible, allCategories, allServices]) => {
      setUsers(allUsers);
      setAssignees(eligible);
      setCategories(allCategories);
      setServices(allServices);
    });
  }, []);

  function updateFilter(key: string, value: string) {
    setFilters((current) => updateWorkbenchFilter(current, key, value));
  }

  function setPage(nextPage: number) {
    setFilters((current) => updateWorkbenchPage(current, nextPage, data?.pages ?? 1));
  }

  async function submitAction() {
    if (!action) return;
    const field = payloadFields[action.action];
    if (field && !payload.trim()) {
      setError(`Заполните поле «${field[1]}»`);
      return;
    }
    setPending(true);
    try {
      const body: Record<string, string> = {};
      if (field) body[field[0]] = payload.trim();
      if (action.action === "assign" || action.action === "reassign") body.assignee_user_id = payload;
      await performWorkbenchAction(action.ticket.ticket_id, action.action, body, action.ticket.active_approval_id);
      setAction(null);
      setPayload("");
      await load({ silent: true });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Действие не выполнено");
      await load({ silent: true });
    } finally {
      setPending(false);
    }
  }

  const hasFilters = Object.entries(filters).some(([key, value]) => !["page", "page_size"].includes(key) && value) || Boolean(search);
  const showInitialSpinner = shouldShowInitialWorkbenchSpinner(loading, Boolean(data));

  return (
    <>
      <PageLayout title="Рабочее место Service Desk" subtitle="Операционная очередь заявок, согласований и SLA">
        <div className="workbench-quick-views">
          {counters && (Object.keys(quickLabels) as WorkbenchQuickView[])
            .filter((key) => counters[key] !== null)
            .map((key) => (
              <Button key={key} variant={filters.quick_view === key ? "primary" : "secondary"} onClick={() => updateFilter("quick_view", key)}>
                {quickLabels[key]} · {counters[key]}
              </Button>
            ))}
        </div>

        <Card>
          <div className="filters workbench-filters">
            <Input label="Поиск" value={search} onChange={(event) => { setSearch(event.target.value); setFilters((current) => ({ ...current, page: "1" })); }} placeholder="Номер, название или услуга" />
            <Select label="Статус" value={filters.status ?? ""} onChange={(event) => updateFilter("status", event.target.value)}>{workbenchStatusOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</Select>
            <Select label="Исполнитель" value={filters.assignee_user_id ?? ""} onChange={(event) => updateFilter("assignee_user_id", event.target.value)}><option value="">Все</option>{assignees.map((u) => <option key={u.id} value={u.id}>{u.display_name}</option>)}</Select>
            <Select label="Заявитель" value={filters.requester_user_id ?? ""} onChange={(event) => updateFilter("requester_user_id", event.target.value)}><option value="">Все</option>{users.map((u) => <option key={u.id} value={u.id}>{u.display_name}</option>)}</Select>
            <Select label="Приоритет" value={filters.priority ?? ""} onChange={(event) => updateFilter("priority", event.target.value)}><option value="">Все</option><option value="low">Низкий</option><option value="medium">Средний</option><option value="high">Высокий</option><option value="critical">Критический</option></Select>
            <Select label="Категория" value={filters.category_id ?? ""} onChange={(event) => updateFilter("category_id", event.target.value)}><option value="">Все</option>{categories.map((c) => <option key={c.id} value={c.id}>{c.title}</option>)}</Select>
            <Select label="Услуга" value={filters.service_id ?? ""} onChange={(event) => updateFilter("service_id", event.target.value)}><option value="">Все</option>{services.filter((s) => !filters.category_id || s.category_id === filters.category_id).map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}</Select>
            <Select label="SLA" value={filters.sla_state ?? ""} onChange={(event) => updateFilter("sla_state", event.target.value)}><option value="">Все</option><option value="no_sla">Без SLA</option><option value="on_track">В норме</option><option value="paused">На паузе</option><option value="warning">Риск</option><option value="breached">Нарушен</option></Select>
            <Select label="Просрочка" value={filters.overdue ?? ""} onChange={(event) => updateFilter("overdue", event.target.value)}><option value="">Все</option><option value="true">Только просроченные</option><option value="false">Без просрочки</option></Select>
            <Input label="Создана с" type="datetime-local" value={filters.created_from ?? ""} onChange={(event) => updateFilter("created_from", event.target.value)} />
            <Input label="Создана по" type="datetime-local" value={filters.created_to ?? ""} onChange={(event) => updateFilter("created_to", event.target.value)} />
            <Button variant="ghost" onClick={() => { setFilters(initialWorkbenchFilters); setSearch(""); }}>Сбросить</Button>
          </div>
        </Card>

        {error && <p className="form-error" role="alert">{error}</p>}
        {showInitialSpinner ? (
          <Spinner label="Загружаем заявки" />
        ) : data?.items.length ? (
          <>
            <ServiceDeskWorkbenchTable items={data.items} onAction={(ticket, selected) => { setAction({ ticket, action: selected }); setPayload(""); }} />
            <div className="workbench-pagination">
              <Button variant="secondary" disabled={filters.page === "1"} onClick={() => setPage(Number(filters.page) - 1)}>Назад</Button>
              <span>Страница {filters.page} из {data.pages || 1} · {data.total} заявок</span>
              <Button variant="secondary" disabled={Number(filters.page) >= data.pages} onClick={() => setPage(Number(filters.page) + 1)}>Далее</Button>
            </div>
          </>
        ) : (
          <EmptyState
            title={hasFilters ? "По выбранным фильтрам ничего не найдено" : "В рабочем месте пока нет заявок"}
            text={hasFilters ? "Измените или сбросьте фильтры." : "Новые операционные заявки появятся здесь."}
          />
        )}
      </PageLayout>

      {action && (
        <Modal title="Действие с заявкой" onClose={() => setAction(null)}>
          <div className="modal-body">
            {action.action === "assign" || action.action === "reassign" ? (
              <Select label="Исполнитель" value={payload} onChange={(event) => setPayload(event.target.value)}>
                <option value="">Выберите</option>{assignees.map((u) => <option key={u.id} value={u.id}>{u.display_name}</option>)}
              </Select>
            ) : payloadFields[action.action] ? (
              <label className="field"><span>{payloadFields[action.action]?.[1]}</span><textarea value={payload} onChange={(event) => setPayload(event.target.value)} /></label>
            ) : (
              <p>Подтвердите действие для заявки {action.ticket.number}.</p>
            )}
            <div className="table-actions">
              <Button disabled={pending || ((action.action === "assign" || action.action === "reassign") && !payload)} onClick={() => void submitAction()}>{pending ? "Выполняем..." : "Подтвердить"}</Button>
              <Button variant="secondary" onClick={() => setAction(null)}>Отмена</Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
}
