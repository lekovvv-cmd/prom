import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Plus, RefreshCw } from "lucide-react";
import { createEscalation, createSlaBinding, createSlaCalendar, createSlaPolicy, getEscalations, getSlaBindings, getSlaCalendars, getSlaPolicies } from "../../../entities/service-desk-sla/api/serviceDeskSlaApi";
import type { BusinessCalendar, EscalationRule, SlaBinding, SlaPolicy } from "../../../entities/service-desk-sla/model/types";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";
import { Header } from "../../../widgets/header/ui/Header";

export function ServiceDeskAdminSlaPage() {
  const [calendars, setCalendars] = useState<BusinessCalendar[]>([]);
  const [policies, setPolicies] = useState<SlaPolicy[]>([]);
  const [bindings, setBindings] = useState<SlaBinding[]>([]);
  const [escalations, setEscalations] = useState<EscalationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { const [c, p, b, e] = await Promise.all([getSlaCalendars(), getSlaPolicies(), getSlaBindings(), getEscalations()]); setCalendars(c); setPolicies(p); setBindings(b); setEscalations(e); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Не удалось загрузить SLA"); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  async function calendarSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    await createSlaCalendar({ name: String(data.get("name")), timezone: String(data.get("timezone")), is_active: true, business_hours: [0,1,2,3,4].flatMap((weekday) => [{ weekday, start_time: String(data.get("morningStart")), end_time: String(data.get("morningEnd")) }, { weekday, start_time: String(data.get("eveningStart")), end_time: String(data.get("eveningEnd")) }]), exceptions: [] }); form.reset(); await load();
  }
  async function policySubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
    await createSlaPolicy({ name: String(data.get("name")), business_calendar_id: String(data.get("calendar")), first_response_minutes: Number(data.get("response")), resolution_minutes: Number(data.get("resolution")), is_active: true, pause_statuses: ["waiting_requester", "waiting_external"].filter((status) => data.get(status)) as SlaPolicy["pause_statuses"] }); form.reset(); await load();
  }
  async function bindingSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget); await createSlaBinding({ name: String(data.get("name")), policy_id: String(data.get("policy")), priority: Number(data.get("priority")), is_active: true, conditions: [{ field: String(data.get("field")), value: String(data.get("value")) }] }); await load();
  }
  async function escalationSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget); await createEscalation(String(data.get("policy")), { metric: String(data.get("metric")) as EscalationRule["metric"], threshold_percent: Number(data.get("threshold")), action_type: "create_in_app_notification", recipient_type: String(data.get("recipient")), is_active: true }); await load();
  }
  return <><Header /><PageLayout title="SLA Service Desk" subtitle="Рабочие календари, policies, bindings и escalation rules." actions={<Button variant="secondary" onClick={() => void load()}><RefreshCw size={16}/>Обновить</Button>}>
    {error ? <p className="form-error">{error}</p> : null}{loading ? <Spinner label="Загружаем SLA"/> : null}
    {!loading ? <div className="service-desk-sla-grid">
      <Card><h2>Рабочий календарь</h2><form className="service-desk-routing-form" onSubmit={(e) => void calendarSubmit(e)}><Input name="name" label="Название" required/><Input name="timezone" label="IANA timezone" defaultValue="Asia/Yekaterinburg" required/><div className="service-desk-sla-times"><Input name="morningStart" label="Начало" type="time" defaultValue="09:00"/><Input name="morningEnd" label="Перерыв с" type="time" defaultValue="13:00"/><Input name="eveningStart" label="Перерыв до" type="time" defaultValue="14:00"/><Input name="eveningEnd" label="Окончание" type="time" defaultValue="18:00"/></div><Button><Plus size={16}/>Создать календарь</Button></form>{calendars.map(c => <p key={c.id}><strong>{c.name}</strong> · {c.timezone} · {c.business_hours.length} интервалов · {c.exceptions.length} исключений</p>)}</Card>
      <Card><h2>SLA policy</h2><form className="service-desk-routing-form" onSubmit={(e) => void policySubmit(e)}><Input name="name" label="Название" required/><Select name="calendar" label="Календарь" required><option value="">Выберите</option>{calendars.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</Select><Input name="response" label="First response, минут" type="number" min="1" required/><Input name="resolution" label="Resolution, минут" type="number" min="1" required/><label><input name="waiting_requester" type="checkbox"/> Пауза: ожидание заявителя</label><label><input name="waiting_external" type="checkbox"/> Пауза: внешнее ожидание</label><Button>Создать policy</Button></form>{policies.map(p=><p key={p.id}><strong>{p.name}</strong> · {p.first_response_minutes}/{p.resolution_minutes} мин.</p>)}</Card>
      <Card><h2>Binding</h2><form className="service-desk-routing-form" onSubmit={(e)=>void bindingSubmit(e)}><Input name="name" label="Название" required/><Select name="policy" label="Policy" required>{policies.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</Select><Input name="priority" label="Приоритет" type="number" defaultValue="100"/><Select name="field" label="Условие"><option value="service_id">Услуга</option><option value="category_id">Категория</option><option value="priority">Приоритет заявки</option><option value="template_version_id">Версия шаблона</option></Select><Input name="value" label="Значение" required/><Button>Создать binding</Button></form>{bindings.length ? bindings.map(b=><p key={b.id}>{b.name} · приоритет {b.priority}</p>) : <EmptyState title="Bindings не заданы" text="Добавьте правило выбора SLA."/>}</Card>
      <Card><h2>Эскалация</h2><form className="service-desk-routing-form" onSubmit={(e)=>void escalationSubmit(e)}><Select name="policy" label="Policy">{policies.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</Select><Select name="metric" label="Метрика"><option value="first_response">First response</option><option value="resolution">Resolution</option></Select><Input name="threshold" label="Threshold, %" type="number" min="1" required/><Select name="recipient" label="Получатель"><option value="assignee">Исполнитель</option><option value="requester">Заявитель</option><option value="service_desk_admin">Администратор SD</option><option value="specific_user">Конкретный пользователь</option></Select><Button>Создать эскалацию</Button></form>{escalations.map(e=><p key={e.id}>{e.metric} · {e.threshold_percent}% · {e.recipient_type}</p>)}</Card>
    </div> : null}
  </PageLayout></>;
}
