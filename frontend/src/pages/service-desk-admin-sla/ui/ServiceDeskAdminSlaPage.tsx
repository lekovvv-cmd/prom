import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from "react";
import { CircleQuestionMark, Pencil, Plus, RefreshCw, Save, Trash2 } from "lucide-react";

import {
  createEscalation,
  createSlaBinding,
  createSlaCalendar,
  createSlaPolicy,
  deleteEscalation,
  getEscalations,
  getSlaBindings,
  getSlaCalendars,
  getSlaPolicies,
  getSlaRecipients,
  updateEscalation,
  updateSlaBinding,
  updateSlaCalendar,
  updateSlaPolicy
} from "../../../entities/service-desk-sla/api/serviceDeskSlaApi";
import type {
  BusinessCalendar,
  CalendarException,
  EscalationRecipientType,
  EscalationRule,
  SlaBinding,
  SlaBindingConditionField,
  SlaPolicy,
  SlaRecipient
} from "../../../entities/service-desk-sla/model/types";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";
import {
  BINDING_FIELD_OPTIONS,
  WEEKDAY_OPTIONS,
  bindingDraftToPayload,
  bindingToDraft,
  calendarDraftToPayload,
  calendarToDraft,
  emptyBindingCondition,
  emptyBindingDraft,
  emptyBusinessHours,
  emptyCalendarDraft,
  emptyCalendarException,
  emptyEscalationDraft,
  emptyPolicyDraft,
  escalationDraftToPayload,
  escalationToDraft,
  policyDraftToPayload,
  policyToDraft,
  type BindingDraft,
  type CalendarDraft,
  type EscalationDraft,
  type PolicyDraft
} from "../model/slaAdminDrafts";

type EditorProps<T> = {
  draft: T;
  editingId: string | null;
  isSaving: boolean;
  onCancel: () => void;
  onChange: (updater: (current: T) => T) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

const recipientLabels: Record<EscalationRecipientType, string> = { assignee: "Исполнитель", requester: "Заявитель", service_desk_admin: "Администратор Service Desk", specific_user: "Конкретный пользователь" };
const metricLabels = { first_response: "Первый ответ", resolution: "Выполнение" } as const;
const conditionLabels = Object.fromEntries(BINDING_FIELD_OPTIONS.map((option) => [option.value, option.label]));

export const SLA_TIMEZONE_OPTIONS = [
  { value: "Europe/Kaliningrad", label: "Калининград (UTC+2)" },
  { value: "Europe/Moscow", label: "Москва (UTC+3)" },
  { value: "Europe/Samara", label: "Самара (UTC+4)" },
  { value: "Asia/Yekaterinburg", label: "Екатеринбург (UTC+5)" },
  { value: "Asia/Omsk", label: "Омск (UTC+6)" },
  { value: "Asia/Novosibirsk", label: "Новосибирск (UTC+7)" },
  { value: "Asia/Irkutsk", label: "Иркутск (UTC+8)" },
  { value: "Asia/Vladivostok", label: "Владивосток (UTC+10)" }
] as const;

export const slaSectionHelp = {
  calendars: "Определяют рабочие часы, выходные и исключения. Счётчики SLA идут только внутри указанных рабочих интервалов.",
  policies: "Задают сроки первого ответа и выполнения, календарь для расчёта и статусы, в которых отсчёт ставится на паузу.",
  bindings: "Связывают политику с заявками. Правила проверяются по приоритету: первое подходящее правило назначает SLA.",
  escalations: "Отправляют уведомление выбранному получателю, когда заявка приближается к нарушению срока."
} as const;

function SlaSectionHeading({ id, title, description, help }: { id: string; title: string; description: string; help: string }) {
  return <div className="service-desk-sla-section-heading">
    <div><h2 id={id}>{title}</h2><p>{description}</p></div>
    <details className="service-desk-sla-help">
      <summary aria-label={`Как работают ${title}`}><CircleQuestionMark size={19} aria-hidden="true" /></summary>
      <p>{help}</p>
    </details>
  </div>;
}

function TimezoneSelect({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const hasKnownValue = SLA_TIMEZONE_OPTIONS.some((option) => option.value === value);

  return (
    <div className="service-desk-sla-timezone-field">
      <Select label="Часовой пояс" value={value} onChange={(event) => onChange(event.target.value)} required>
        {!hasKnownValue ? <option value={value}>{value}</option> : null}
        {SLA_TIMEZONE_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </Select>
      <p>По нему рассчитываются рабочие часы и сроки заявок.</p>
    </div>
  );
}

function SlaAdvancedSettings({
  title,
  description,
  children,
  open,
  onOpenChange
}: {
  title: string;
  description: string;
  children: ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}) {
  return (
    <details className="service-desk-sla-advanced-settings" open={open} onToggle={(event) => onOpenChange?.(event.currentTarget.open)}>
      <summary>
        <span><strong>{title}</strong><small>{description}</small></span>
        <span className="service-desk-sla-advanced-action">Настроить</span>
      </summary>
      <div className="service-desk-sla-advanced-content">{children}</div>
    </details>
  );
}

function SlaWorkflowOverview() {
  return <ol className="service-desk-sla-workflow" aria-label="Как настроить SLA">
    <li><strong>1. Рабочее время</strong><span>Когда команда обрабатывает заявки.</span></li>
    <li><strong>2. Сроки</strong><span>Сколько есть времени на ответ и решение.</span></li>
    <li><strong>3. Применение</strong><span>Для каких заявок действуют сроки.</span></li>
    <li><strong>4. Уведомления</strong><span>Необязательные предупреждения о риске.</span></li>
  </ol>;
}

function ActiveCheckbox({
  checked,
  label,
  onChange
}: {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="service-desk-routing-check">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

function FormActions({ editingId, isSaving, onCancel }: Pick<EditorProps<unknown>, "editingId" | "isSaving" | "onCancel">) {
  return (
    <div className="form-actions">
      <Button type="submit" disabled={isSaving}>
        <Save size={16} /> {isSaving ? "Сохраняем…" : editingId ? "Сохранить изменения" : "Создать"}
      </Button>
      {editingId ? (
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isSaving}>
          Отмена
        </Button>
      ) : null}
    </div>
  );
}

function CalendarEditor({ draft, editingId, isSaving, onCancel, onChange, onSubmit }: EditorProps<CalendarDraft>) {
  const updateException = (index: number, patch: Partial<CalendarException>) => {
    onChange((current) => ({
      ...current,
      exceptions: current.exceptions.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item
      )
    }));
  };

  return (
    <Card className="service-desk-sla-editor-card">
      <div className="service-desk-sla-card-heading">
        <div><span className="service-desk-eyebrow">Календарь</span><h2>{editingId ? "Редактирование календаря" : "Новый календарь"}</h2></div>
      </div>
      <form className="service-desk-sla-form" onSubmit={onSubmit}>
        <div className="service-desk-sla-form-grid">
          <Input label="Название календаря" value={draft.name} onChange={(event) => onChange((current) => ({ ...current, name: event.target.value }))} placeholder="Например, рабочее время Service Desk" required />
          <TimezoneSelect value={draft.timezone} onChange={(timezone) => onChange((current) => ({ ...current, timezone }))} />
        </div>
        <ActiveCheckbox checked={draft.isActive} label="Календарь активен" onChange={(isActive) => onChange((current) => ({ ...current, isActive }))} />

        <div className="service-desk-sla-form-section">
          <div className="service-desk-sla-card-heading">
            <div><h3>Рабочее время</h3><p>Укажите, в какие часы SLA должен отсчитываться. Если в течение дня есть перерыв, добавьте ещё один интервал.</p></div>
            <Button type="button" variant="secondary" onClick={() => onChange((current) => ({ ...current, businessHours: [...current.businessHours, emptyBusinessHours()] }))}>
              <Plus size={16} /> Интервал
            </Button>
          </div>
          <div className="service-desk-sla-row-list">
            {draft.businessHours.map((interval, index) => (
              <div className="service-desk-sla-interval-row" key={`hours-${index}`}>
                <Select aria-label={`День недели ${index + 1}`} value={interval.weekday} onChange={(event) => onChange((current) => ({ ...current, businessHours: current.businessHours.map((item, itemIndex) => itemIndex === index ? { ...item, weekday: Number(event.target.value) } : item) }))}>
                  {WEEKDAY_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </Select>
                <Input aria-label={`Начало интервала ${index + 1}`} type="time" value={interval.start_time} onChange={(event) => onChange((current) => ({ ...current, businessHours: current.businessHours.map((item, itemIndex) => itemIndex === index ? { ...item, start_time: event.target.value } : item) }))} required />
                <Input aria-label={`Конец интервала ${index + 1}`} type="time" value={interval.end_time} onChange={(event) => onChange((current) => ({ ...current, businessHours: current.businessHours.map((item, itemIndex) => itemIndex === index ? { ...item, end_time: event.target.value } : item) }))} required />
                <Button type="button" variant="ghost" aria-label={`Удалить рабочий интервал ${index + 1}`} disabled={draft.businessHours.length === 1} onClick={() => onChange((current) => ({ ...current, businessHours: current.businessHours.filter((_, itemIndex) => itemIndex !== index) }))}><Trash2 size={16} /></Button>
              </div>
            ))}
          </div>
        </div>

        <SlaAdvancedSettings title="Праздники и исключения" description="Добавьте их, только если обычного графика недостаточно.">
          <div className="service-desk-sla-form-section service-desk-sla-advanced-section">
            <div className="service-desk-sla-card-heading">
              <div><h3>Исключения из графика</h3><p>Праздники, дополнительные рабочие дни и особые часы.</p></div>
              <Button type="button" variant="secondary" onClick={() => onChange((current) => ({ ...current, exceptions: [...current.exceptions, emptyCalendarException()] }))}>
                <Plus size={16} /> Исключение
              </Button>
            </div>
            {draft.exceptions.length === 0 ? <p className="muted">Исключений пока нет.</p> : (
              <div className="service-desk-sla-row-list">
                {draft.exceptions.map((exception, index) => (
                  <div className={`service-desk-sla-exception-row${exception.type === "custom_hours" ? " is-custom" : ""}`} key={`exception-${index}`}>
                    <Input aria-label={`Дата исключения ${index + 1}`} type="date" value={exception.date} onChange={(event) => updateException(index, { date: event.target.value })} required />
                    <Select aria-label={`Тип исключения ${index + 1}`} value={exception.type} onChange={(event) => updateException(index, { type: event.target.value as CalendarException["type"], start_time: undefined, end_time: undefined })}>
                      <option value="holiday">Выходной день</option>
                      <option value="working_day">Рабочий день</option>
                      <option value="custom_hours">Особые часы</option>
                    </Select>
                    {exception.type === "custom_hours" ? <>
                      <Input aria-label={`Начало исключения ${index + 1}`} type="time" value={exception.start_time ?? ""} onChange={(event) => updateException(index, { start_time: event.target.value })} required />
                      <Input aria-label={`Конец исключения ${index + 1}`} type="time" value={exception.end_time ?? ""} onChange={(event) => updateException(index, { end_time: event.target.value })} required />
                    </> : null}
                    <Input aria-label={`Описание исключения ${index + 1}`} placeholder="Например, новогодние каникулы" value={exception.description ?? ""} onChange={(event) => updateException(index, { description: event.target.value })} />
                    <Button type="button" variant="ghost" aria-label={`Удалить исключение ${index + 1}`} onClick={() => onChange((current) => ({ ...current, exceptions: current.exceptions.filter((_, itemIndex) => itemIndex !== index) }))}><Trash2 size={16} /></Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </SlaAdvancedSettings>
        <FormActions editingId={editingId} isSaving={isSaving} onCancel={onCancel} />
      </form>
    </Card>
  );
}

function PolicyEditor({ calendars, draft, editingId, isSaving, onCancel, onChange, onSubmit }: EditorProps<PolicyDraft> & { calendars: BusinessCalendar[] }) {
  const togglePause = (status: SlaPolicy["pause_statuses"][number], checked: boolean) => {
    onChange((current) => ({
      ...current,
      pauseStatuses: checked
        ? [...new Set([...current.pauseStatuses, status])]
        : current.pauseStatuses.filter((item) => item !== status)
    }));
  };
  return (
    <Card className="service-desk-sla-editor-card">
      <div className="service-desk-sla-card-heading"><div><span className="service-desk-eyebrow">Политика SLA</span><h2>{editingId ? "Редактирование политики SLA" : "Новая политика SLA"}</h2></div></div>
      <form className="service-desk-sla-form" onSubmit={onSubmit}>
        <Input label="Название политики" value={draft.name} onChange={(event) => onChange((current) => ({ ...current, name: event.target.value }))} placeholder="Например, стандартный срок" required />
        <Select label="Рабочий календарь" value={draft.calendarId} onChange={(event) => onChange((current) => ({ ...current, calendarId: event.target.value }))} required>
          <option value="">Выберите календарь</option>{calendars.map((calendar) => <option key={calendar.id} value={calendar.id}>{calendar.name}</option>)}
        </Select>
        <div className="service-desk-sla-form-grid">
          <Input label="Срок первого ответа, минут" type="number" min="1" value={draft.firstResponseMinutes} onChange={(event) => onChange((current) => ({ ...current, firstResponseMinutes: event.target.value }))} required />
          <Input label="Срок решения, минут" type="number" min="1" value={draft.resolutionMinutes} onChange={(event) => onChange((current) => ({ ...current, resolutionMinutes: event.target.value }))} required />
        </div>
        <p className="service-desk-sla-inline-hint">Сроки считаются только внутри выбранного рабочего календаря.</p>
        <ActiveCheckbox checked={draft.isActive} label="Использовать эту политику" onChange={(isActive) => onChange((current) => ({ ...current, isActive }))} />
        <SlaAdvancedSettings title="Дополнительные параметры" description="Паузы и описание нужны не для каждого SLA.">
          <div className="service-desk-sla-advanced-section service-desk-sla-form">
            <label className="field"><span>Описание для команды</span><textarea value={draft.description} onChange={(event) => onChange((current) => ({ ...current, description: event.target.value }))} /></label>
            <div className="service-desk-sla-check-list">
              <ActiveCheckbox checked={draft.pauseStatuses.includes("waiting_requester")} label="Останавливать срок, когда ждём заявителя" onChange={(checked) => togglePause("waiting_requester", checked)} />
              <ActiveCheckbox checked={draft.pauseStatuses.includes("waiting_external")} label="Останавливать срок при внешнем ожидании" onChange={(checked) => togglePause("waiting_external", checked)} />
            </div>
          </div>
        </SlaAdvancedSettings>
        <FormActions editingId={editingId} isSaving={isSaving} onCancel={onCancel} />
      </form>
    </Card>
  );
}

function BindingEditor({ policies, draft, editingId, isSaving, onCancel, onChange, onSubmit }: EditorProps<BindingDraft> & { policies: SlaPolicy[] }) {
  return (
    <Card className="service-desk-sla-editor-card">
      <div className="service-desk-sla-card-heading"><div><span className="service-desk-eyebrow">Правило применения</span><h2>{editingId ? "Редактирование правила применения" : "Новое правило применения"}</h2></div></div>
      <form className="service-desk-sla-form" onSubmit={onSubmit}>
        <Input label="Название правила" value={draft.name} onChange={(event) => onChange((current) => ({ ...current, name: event.target.value }))} placeholder="Например, заявки высокой важности" required />
        <Select label="Применять политику" value={draft.policyId} onChange={(event) => onChange((current) => ({ ...current, policyId: event.target.value }))} required><option value="">Выберите политику</option>{policies.map((policy) => <option key={policy.id} value={policy.id}>{policy.name}</option>)}</Select>
        <ActiveCheckbox checked={draft.isActive} label="Использовать это правило" onChange={(isActive) => onChange((current) => ({ ...current, isActive }))} />
        <div className="service-desk-sla-form-section">
          <div className="service-desk-sla-card-heading"><div><h3>Для каких заявок</h3><p>Выберите признаки заявки. Все добавленные условия должны совпасть.</p></div><Button type="button" variant="secondary" onClick={() => onChange((current) => ({ ...current, conditions: [...current.conditions, emptyBindingCondition()] }))}><Plus size={16} /> Ещё условие</Button></div>
          <div className="service-desk-sla-row-list">
            {draft.conditions.map((condition, index) => (
              <div className={`service-desk-sla-condition-row${condition.field === "field_value" ? " is-field-value" : ""}`} key={`condition-${index}`}>
                <Select aria-label={`Тип условия ${index + 1}`} value={condition.field} onChange={(event) => { const field = event.target.value as SlaBindingConditionField; onChange((current) => ({ ...current, conditions: current.conditions.map((item, itemIndex) => itemIndex === index ? { field, value: "", field_key: field === "field_value" ? "" : undefined } : item) })); }}>
                  {BINDING_FIELD_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </Select>
                {condition.field === "field_value" ? <Input aria-label={`Ключ поля ${index + 1}`} placeholder="Ключ поля" value={condition.field_key ?? ""} onChange={(event) => onChange((current) => ({ ...current, conditions: current.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, field_key: event.target.value } : item) }))} required /> : null}
                {condition.field === "priority" ? <Select aria-label={`Значение условия ${index + 1}`} value={condition.value} onChange={(event) => onChange((current) => ({ ...current, conditions: current.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, value: event.target.value } : item) }))} required><option value="">Выберите приоритет</option><option value="low">Низкий</option><option value="medium">Средний</option><option value="high">Высокий</option><option value="critical">Критический</option></Select> : <Input aria-label={`Значение условия ${index + 1}`} placeholder="Значение" value={condition.value} onChange={(event) => onChange((current) => ({ ...current, conditions: current.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, value: event.target.value } : item) }))} required />}
                <Button type="button" variant="ghost" aria-label={`Удалить условие ${index + 1}`} disabled={draft.conditions.length === 1} onClick={() => onChange((current) => ({ ...current, conditions: current.conditions.filter((_, itemIndex) => itemIndex !== index) }))}><Trash2 size={16} /></Button>
              </div>
            ))}
          </div>
        </div>
        <SlaAdvancedSettings title="Очередность правила" description="Обычно менять не нужно: правила с меньшим числом срабатывают раньше.">
          <div className="service-desk-sla-advanced-section service-desk-sla-form">
            <Input label="Порядок применения" type="number" min="0" value={draft.priority} onChange={(event) => onChange((current) => ({ ...current, priority: event.target.value }))} required />
            <p className="service-desk-sla-inline-hint">Оставьте 100, если это обычное правило. Например, 10 можно задать для исключения, которое важнее остальных.</p>
          </div>
        </SlaAdvancedSettings>
        <FormActions editingId={editingId} isSaving={isSaving} onCancel={onCancel} />
      </form>
    </Card>
  );
}

function EscalationEditor({ policies, recipients, draft, editingId, isSaving, onCancel, onChange, onSubmit }: EditorProps<EscalationDraft> & { policies: SlaPolicy[]; recipients: SlaRecipient[] }) {
  return (
    <Card className="service-desk-sla-editor-card">
      <div className="service-desk-sla-card-heading"><div><span className="service-desk-eyebrow">Эскалация</span><h2>{editingId ? "Редактирование эскалации" : "Новая эскалация"}</h2></div></div>
      <form className="service-desk-sla-form" onSubmit={onSubmit}>
        <Select label="Политика SLA" value={draft.policyId} disabled={editingId !== null} onChange={(event) => onChange((current) => ({ ...current, policyId: event.target.value }))} required><option value="">Выберите политику</option>{policies.map((policy) => <option key={policy.id} value={policy.id}>{policy.name}</option>)}</Select>
        <div className="service-desk-sla-form-grid">
        <Select label="Метрика" value={draft.metric} onChange={(event) => onChange((current) => ({ ...current, metric: event.target.value as EscalationDraft["metric"] }))}><option value="first_response">Первый ответ</option><option value="resolution">Выполнение</option></Select>
        <Input label="Порог, %" type="number" min="1" value={draft.thresholdPercent} onChange={(event) => onChange((current) => ({ ...current, thresholdPercent: event.target.value }))} required />
        </div>
        <Select label="Действие" value={draft.actionType} onChange={(event) => onChange((current) => ({ ...current, actionType: event.target.value as EscalationDraft["actionType"] }))}><option value="create_in_app_notification">Уведомление в системе</option><option value="email_notification_when_available">Email при доступности канала</option></Select>
        <Select label="Получатель" value={draft.recipientType} onChange={(event) => { const recipientType = event.target.value as EscalationRecipientType; onChange((current) => ({ ...current, recipientType, recipientUserId: recipientType === "specific_user" ? current.recipientUserId : "" })); }}><option value="assignee">Исполнитель</option><option value="requester">Заявитель</option><option value="service_desk_admin">Администраторы Service Desk</option><option value="specific_user">Конкретный пользователь</option></Select>
        {draft.recipientType === "specific_user" ? <Select label="Пользователь-получатель" value={draft.recipientUserId} onChange={(event) => onChange((current) => ({ ...current, recipientUserId: event.target.value }))} required><option value="">Выберите пользователя</option>{recipients.map((recipient) => <option key={recipient.id} value={recipient.id}>{recipient.display_name} — {recipient.email}</option>)}</Select> : null}
        <ActiveCheckbox checked={draft.isActive} label="Эскалация активна" onChange={(isActive) => onChange((current) => ({ ...current, isActive }))} />
        <FormActions editingId={editingId} isSaving={isSaving} onCancel={onCancel} />
      </form>
    </Card>
  );
}

function EntityList({ children, emptyTitle }: { children: React.ReactNode; emptyTitle?: string }) {
  return <div className="service-desk-sla-entity-list">{children ?? <EmptyState title={emptyTitle ?? "Нет данных"} />}</div>;
}

function errorMessage(reason: unknown): string {
  return reason instanceof Error ? reason.message : "Не удалось сохранить настройки SLA";
}

export function ServiceDeskAdminSlaPage() {
  const [calendars, setCalendars] = useState<BusinessCalendar[]>([]);
  const [policies, setPolicies] = useState<SlaPolicy[]>([]);
  const [bindings, setBindings] = useState<SlaBinding[]>([]);
  const [escalations, setEscalations] = useState<EscalationRule[]>([]);
  const [recipients, setRecipients] = useState<SlaRecipient[]>([]);
  const [calendarDraft, setCalendarDraft] = useState<CalendarDraft>(emptyCalendarDraft);
  const [policyDraft, setPolicyDraft] = useState<PolicyDraft>(() => emptyPolicyDraft());
  const [bindingDraft, setBindingDraft] = useState<BindingDraft>(() => emptyBindingDraft());
  const [escalationDraft, setEscalationDraft] = useState<EscalationDraft>(() => emptyEscalationDraft());
  const [editingCalendarId, setEditingCalendarId] = useState<string | null>(null);
  const [editingPolicyId, setEditingPolicyId] = useState<string | null>(null);
  const [editingBindingId, setEditingBindingId] = useState<string | null>(null);
  const [editingEscalationId, setEditingEscalationId] = useState<string | null>(null);
  const [isEscalationEditorOpen, setEscalationEditorOpen] = useState(false);
  const [savingEditor, setSavingEditor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextCalendars, nextPolicies, nextBindings, nextEscalations, nextRecipients] = await Promise.all([
        getSlaCalendars(), getSlaPolicies(), getSlaBindings(), getEscalations(), getSlaRecipients()
      ]);
      setCalendars(nextCalendars);
      setPolicies(nextPolicies);
      setBindings(nextBindings);
      setEscalations(nextEscalations);
      setRecipients(nextRecipients);
      setPolicyDraft((current) => current.calendarId || nextCalendars.length === 0 ? current : { ...current, calendarId: nextCalendars[0].id });
      setBindingDraft((current) => current.policyId || nextPolicies.length === 0 ? current : { ...current, policyId: nextPolicies[0].id });
      setEscalationDraft((current) => current.policyId || nextPolicies.length === 0 ? current : { ...current, policyId: nextPolicies[0].id });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Не удалось загрузить настройки SLA");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const resetCalendar = () => { setEditingCalendarId(null); setCalendarDraft(emptyCalendarDraft()); };
  const resetPolicy = () => { setEditingPolicyId(null); setPolicyDraft(emptyPolicyDraft(calendars[0]?.id)); };
  const resetBinding = () => { setEditingBindingId(null); setBindingDraft(emptyBindingDraft(policies[0]?.id)); };
  const resetEscalation = () => { setEditingEscalationId(null); setEscalationDraft(emptyEscalationDraft(policies[0]?.id)); };

  const persist = async (editor: string, operation: () => Promise<unknown>, reset: () => void) => {
    try {
      setSavingEditor(editor);
      setError(null);
      await operation();
      reset();
      await load();
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setSavingEditor(null);
    }
  };

  const submitCalendar = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const payload = calendarDraftToPayload(calendarDraft); void persist("calendar", () => editingCalendarId ? updateSlaCalendar(editingCalendarId, payload) : createSlaCalendar(payload), resetCalendar); };
  const submitPolicy = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const payload = policyDraftToPayload(policyDraft); void persist("policy", () => editingPolicyId ? updateSlaPolicy(editingPolicyId, payload) : createSlaPolicy(payload), resetPolicy); };
  const submitBinding = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const payload = bindingDraftToPayload(bindingDraft); void persist("binding", () => editingBindingId ? updateSlaBinding(editingBindingId, payload) : createSlaBinding(payload), resetBinding); };
  const submitEscalation = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); const payload = escalationDraftToPayload(escalationDraft); void persist("escalation", () => editingEscalationId ? updateEscalation(editingEscalationId, payload) : createEscalation(escalationDraft.policyId, payload), resetEscalation); };

  const removeEscalation = async (rule: EscalationRule) => {
    try {
      setSavingEditor("escalation");
      setError(null);
      await deleteEscalation(rule.id);
      setEscalations((current) => current.filter((item) => item.id !== rule.id));
      resetEscalation();
    } catch (reason) {
      setError(errorMessage(reason));
    } finally {
      setSavingEditor(null);
    }
  };

  return (
    <PageLayout title="Настройка SLA" subtitle="Настройте рабочее время, сроки и предупреждения для заявок в одном месте." actions={<Button variant="secondary" onClick={() => void load()} disabled={loading}><RefreshCw size={16} /> Обновить</Button>}>
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      {loading ? <Spinner label="Загружаем настройки SLA" /> : (
        <div className="service-desk-sla-sections">
          <SlaWorkflowOverview />
          <section className="service-desk-sla-section" aria-labelledby="sla-calendars-title"><SlaSectionHeading id="sla-calendars-title" title="Рабочее время" description="Укажите часы, выходные и исключения для расчёта SLA." help={slaSectionHelp.calendars} /><div className="service-desk-sla-layout"><CalendarEditor draft={calendarDraft} editingId={editingCalendarId} isSaving={savingEditor === "calendar"} onCancel={resetCalendar} onChange={setCalendarDraft} onSubmit={submitCalendar} /><EntityList>{calendars.length ? calendars.map((calendar) => <Card className="service-desk-sla-summary-card" key={calendar.id}><div className="service-desk-sla-card-heading"><div><span className={calendar.is_active ? "status-badge status-active" : "status-badge status-archived"}>{calendar.is_active ? "Активен" : "Выключен"}</span><h3>{calendar.name}</h3><p>{calendar.timezone} · {calendar.business_hours.length} интервалов · {calendar.exceptions.length} исключений</p></div><Button variant="secondary" onClick={() => { setEditingCalendarId(calendar.id); setCalendarDraft(calendarToDraft(calendar)); }}><Pencil size={16} /> Изменить</Button></div></Card>) : <EmptyState title="Рабочее время ещё не настроено" text="Добавьте расписание команды, чтобы считать сроки заявок." />}</EntityList></div></section>
          <section className="service-desk-sla-section" aria-labelledby="sla-policies-title"><SlaSectionHeading id="sla-policies-title" title="Сроки SLA" description="Задайте срок первого ответа и срок решения для рабочего времени." help={slaSectionHelp.policies} /><div className="service-desk-sla-layout"><PolicyEditor calendars={calendars} draft={policyDraft} editingId={editingPolicyId} isSaving={savingEditor === "policy"} onCancel={resetPolicy} onChange={setPolicyDraft} onSubmit={submitPolicy} /><EntityList>{policies.length ? policies.map((policy) => <Card className="service-desk-sla-summary-card" key={policy.id}><div className="service-desk-sla-card-heading"><div><span className={policy.is_active ? "status-badge status-active" : "status-badge status-archived"}>{policy.is_active ? "Активна" : "Выключена"}</span><h3>{policy.name}</h3><p>Первый ответ: {policy.first_response_minutes} мин · Выполнение: {policy.resolution_minutes} мин</p><p className="muted">Паузы: {policy.pause_statuses.join(", ") || "нет"}</p></div><Button variant="secondary" onClick={() => { setEditingPolicyId(policy.id); setPolicyDraft(policyToDraft(policy)); }}><Pencil size={16} /> Изменить</Button></div></Card>) : <EmptyState title="Сроки SLA пока не настроены" />}</EntityList></div></section>
          <section className="service-desk-sla-section" aria-labelledby="sla-bindings-title"><SlaSectionHeading id="sla-bindings-title" title="Где применять SLA" description="Выберите, к каким заявкам применять каждый срок." help={slaSectionHelp.bindings} /><div className="service-desk-sla-layout"><BindingEditor policies={policies} draft={bindingDraft} editingId={editingBindingId} isSaving={savingEditor === "binding"} onCancel={resetBinding} onChange={setBindingDraft} onSubmit={submitBinding} /><EntityList>{bindings.length ? bindings.map((binding) => <Card className="service-desk-sla-summary-card" key={binding.id}><div className="service-desk-sla-card-heading"><div><span className={binding.is_active ? "status-badge status-active" : "status-badge status-archived"}>{binding.is_active ? "Активно" : "Выключено"}</span><h3>{binding.name}</h3><p>Порядок {binding.priority} · {binding.conditions.length} условий</p><ul>{binding.conditions.map((condition, index) => <li key={`${binding.id}-${index}`}>{conditionLabels[condition.field] ?? "Условие"}{condition.field_key ? ` · ключ поля: ${condition.field_key}` : ""}: {condition.value}</li>)}</ul></div><Button variant="secondary" onClick={() => { setEditingBindingId(binding.id); setBindingDraft(bindingToDraft(binding)); }}><Pencil size={16} /> Изменить</Button></div></Card>) : <EmptyState title="Правил применения SLA пока нет" text="Добавьте правило выбора SLA." />}</EntityList></div></section>
          <section className="service-desk-sla-section" aria-labelledby="sla-escalations-title"><SlaSectionHeading id="sla-escalations-title" title="Уведомления о риске" description="Необязательные предупреждения для ответственных до нарушения срока." help={slaSectionHelp.escalations} /><SlaAdvancedSettings title="Настроить уведомление" description="Добавьте его, если хотите предупредить коллег заранее." open={isEscalationEditorOpen} onOpenChange={setEscalationEditorOpen}><EscalationEditor policies={policies} recipients={recipients} draft={escalationDraft} editingId={editingEscalationId} isSaving={savingEditor === "escalation"} onCancel={resetEscalation} onChange={setEscalationDraft} onSubmit={submitEscalation} /></SlaAdvancedSettings><EntityList>{escalations.length ? escalations.map((rule) => <Card className="service-desk-sla-summary-card" key={rule.id}><div className="service-desk-sla-card-heading"><div><span className={rule.is_active ? "status-badge status-active" : "status-badge status-archived"}>{rule.is_active ? "Активна" : "Выключена"}</span><h3>{metricLabels[rule.metric]} · {rule.threshold_percent}%</h3><p>{recipientLabels[rule.recipient_type]}{rule.recipient_user_id ? ` · ${recipients.find((item) => item.id === rule.recipient_user_id)?.display_name ?? "Пользователь"}` : ""}</p></div><div className="form-actions"><Button variant="secondary" onClick={() => { setEscalationEditorOpen(true); setEditingEscalationId(rule.id); setEscalationDraft(escalationToDraft(rule)); }}><Pencil size={16} /> Изменить</Button><Button variant="danger" onClick={() => void removeEscalation(rule)}><Trash2 size={16} /> Удалить</Button></div></div></Card>) : <EmptyState title="Уведомлений пока нет" />}</EntityList></section>
        </div>
      )}
    </PageLayout>
  );
}
