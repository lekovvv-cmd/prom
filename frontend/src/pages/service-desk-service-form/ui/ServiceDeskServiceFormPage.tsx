import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { FileText, Save, Send } from "lucide-react";

import { getServiceDeskService, getServiceDeskServiceForm } from "../../../entities/service-desk-catalog/api/serviceDeskCatalogApi";
import type { ServiceDeskPublishedForm, ServiceDeskService, ServiceDeskTemplateField } from "../../../entities/service-desk-catalog/model/types";
import { getFieldOptions, isEmpty, matchesRules, type FormValues } from "../../../entities/service-desk-catalog/model/rules";
import { getWorkbenchUsers } from "../../../entities/service-desk-workbench/api/serviceDeskWorkbenchApi";
import { getServiceDeskTicket, getServiceDeskTicketForm, listServiceDeskFieldAttachments, uploadServiceDeskFieldAttachment, createServiceDeskDraft, submitServiceDeskDraft, updateServiceDeskDraft } from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import type { ServiceDeskAttachment, ServiceDeskPriority, ServiceDeskTicket } from "../../../entities/service-desk-ticket/model/types";
import { ApiError, normalizeApiErrorMessage } from "../../../shared/api/client";
import { FileInput } from "../../../entities/attachment/ui/FileInput";
import { useAuth } from "../../../app/providers/AppProviders";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";
import { Header } from "../../../widgets/header/ui/Header";

type FieldErrors = Record<string, string>;
type Users = Array<{ id: string; display_name: string }>;

export function ServiceDeskServiceFormPage() {
  const { serviceId, ticketId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [service, setService] = useState<ServiceDeskService | null>(null);
  const [form, setForm] = useState<ServiceDeskPublishedForm | null>(null);
  const [values, setValues] = useState<FormValues>({});
  const [filesByField, setFilesByField] = useState<Record<string, File[]>>({});
  const [existingByField, setExistingByField] = useState<Record<string, ServiceDeskAttachment[]>>({});
  const [users, setUsers] = useState<Users>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<ServiceDeskPriority>("medium");
  const [draft, setDraft] = useState<ServiceDeskTicket | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<"save" | "submit" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const ticket = ticketId ? await getServiceDeskTicket(ticketId) : null;
        const resolvedServiceId = ticket?.service_id ?? serviceId;
        if (!resolvedServiceId) return;
        const [serviceItem, formData] = await Promise.all([
          getServiceDeskService(resolvedServiceId),
          ticketId ? getServiceDeskTicketForm(ticketId) : getServiceDeskServiceForm(resolvedServiceId),
        ]);
        if (!active) return;
        setService(serviceItem);
        setForm(formData);
        const settings = formData.template_version.system_settings;
        setTitle(ticket?.title ?? settings.default_title ?? serviceItem.title);
        setDescription(ticket?.description ?? "");
        setPriority(ticket?.priority ?? "medium");
        setValues(ticket?.field_values ?? {});
        setDraft(ticket);
        if (ticketId && ticket) {
          const fileFields = formData.fields.filter((field) => field.field_type === "file");
          const entries = await Promise.all(fileFields.map(async (field) => [field.key, await listServiceDeskFieldAttachments(ticket.id, field.key)] as const));
          if (active) setExistingByField(Object.fromEntries(entries));
        }
        if (formData.fields.some((field) => field.field_type === "user")) {
          const options = await getWorkbenchUsers(false);
          if (active) setUsers(options);
        }
      } catch (reason: unknown) {
        if (active) setError(reason instanceof Error ? reason.message : "Не удалось загрузить форму услуги");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => { active = false; };
  }, [serviceId, ticketId]);

  const visibleFields = useMemo(() => (form?.fields ?? []).filter((field) => matchesRules(field.visibility_rules, values, true)).sort((left, right) => left.position - right.position), [form, values]);

  const updateValue = useCallback((key: string, value: unknown) => {
    setValues((current) => ({ ...current, [key]: value }));
    setFieldErrors((current) => { const next = { ...current }; delete next[key]; return next; });
  }, []);

  function validate(forSubmit: boolean) {
    const errors: FieldErrors = {};
    if (forSubmit && title.trim().length < 2) errors.title = "Укажите тему заявки";
    if (forSubmit && form?.template_version.system_settings.is_description_required !== false && !description.trim()) errors.description = "Заполните описание заявки";
    visibleFields.forEach((field) => {
      const required = field.is_required || matchesRules(field.required_rules, values, false);
      const value = values[field.key];
      const files = filesByField[field.key] ?? [];
      const existing = existingByField[field.key] ?? [];
      if (forSubmit && required && isEmpty(field.field_type === "file" ? [...files, ...existing] : value)) errors[field.key] = "Заполните обязательное поле";
      if (forSubmit && field.field_type === "email" && value && !/^\S+@\S+\.\S+$/.test(String(value))) errors[field.key] = "Укажите корректный email";
      if (forSubmit && field.field_type === "number" && value !== undefined && value !== "" && Number.isNaN(Number(value))) errors[field.key] = "Укажите число";
    });
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function persistDraft(submitAfter: boolean) {
    if (!form || !service) return;
    if (submitAfter && !validate(true)) return;
    if (!token) { navigate("/login"); return; }
    setPending(submitAfter ? "submit" : "save");
    setError(null);
    try {
      const common = { title: title.trim() || service.title, description, priority, field_values: values };
      let current: ServiceDeskTicket;
      if (draft) current = await updateServiceDeskDraft(draft.id, common);
      else current = await createServiceDeskDraft({ service_id: service.id, template_version_id: form.template_version.id, ...common });
      setDraft(current);
      for (const [fieldKey, files] of Object.entries(filesByField)) {
        for (const file of files) await uploadServiceDeskFieldAttachment(current.id, fieldKey, file);
      }
      setFilesByField({});
      if (submitAfter) {
        current = await submitServiceDeskDraft(current.id);
        navigate(`/service-desk/tickets/${current.id}`);
      } else {
        setError("Черновик сохранён. Его можно отправить позже из раздела «Мои заявки».");
      }
    } catch (reason: unknown) {
      if (reason instanceof ApiError && reason.details && typeof reason.details === "object" && "detail" in reason.details) {
        const detail = (reason.details as { detail?: unknown }).detail;
        if (detail && typeof detail === "object" && "errors" in detail && Array.isArray((detail as { errors?: unknown }).errors)) {
          const next: FieldErrors = {};
          for (const item of (detail as { errors: Array<{ field_key?: unknown; message?: unknown }> }).errors) if (typeof item.field_key === "string") next[item.field_key] = typeof item.message === "string" ? item.message : "Проверьте поле";
          setFieldErrors(next);
        }
      }
      setError(reason instanceof Error ? reason.message : normalizeApiErrorMessage(null));
    } finally {
      setPending(null);
    }
  }

  return <><Header /><PageLayout title={service?.title ?? "Услуга Service Desk"} subtitle={service ? `${service.category?.title ?? "Каталог"} · заполните форму заявки` : undefined}>
    {loading ? <Spinner label="Загружаем форму услуги" /> : error && !form ? <Card><p className="form-error" role="alert">{error}</p><Link className="button button-secondary" to="/service-desk">Вернуться в каталог</Link></Card> : form && service ? <div className="service-desk-form-layout"><Card className="service-desk-form-card"><div className="service-desk-form-intro"><span className="service-desk-eyebrow"><FileText size={14} aria-hidden="true" /> Форма заявки · версия {form.template_version.version}</span><p>{service.description ?? service.short_description}</p>{form.template_version.system_settings.help_text ? <p className="muted">{form.template_version.system_settings.help_text}</p> : null}</div>
      {!token ? <Card><p>Для сохранения заявки войдите в PROM.</p><Link className="button" to="/login">Войти</Link></Card> : null}
      <div className="service-desk-form-grid"><Input label="Тема заявки" value={title} disabled={form.template_version.system_settings.is_title_editable === false} onChange={(event) => setTitle(event.target.value)} aria-invalid={Boolean(fieldErrors.title)} /><label className="field field-wide"><span>Описание {form.template_version.system_settings.is_description_required !== false ? <sup>*</sup> : null}</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={5} aria-invalid={Boolean(fieldErrors.description)} /></label><Select label="Приоритет" value={priority} onChange={(event) => setPriority(event.target.value as ServiceDeskPriority)}><option value="low">Низкий</option><option value="medium">Средний</option><option value="high">Высокий</option><option value="critical">Критический</option></Select>
        {visibleFields.map((field) => <DynamicField key={field.key} field={field} value={values[field.key]} files={filesByField[field.key] ?? []} existingAttachments={existingByField[field.key] ?? []} users={users} required={field.is_required || matchesRules(field.required_rules, values, false)} error={fieldErrors[field.key]} onChange={updateValue} onFilesChange={(files) => setFilesByField((current) => ({ ...current, [field.key]: files }))} />)}
      </div>{error && form ? <p className={error.startsWith("Черновик") ? "success-text" : "form-error"} role="alert">{error}</p> : null}<div className="form-actions"><Button variant="secondary" disabled={!token || pending !== null} onClick={() => void persistDraft(false)}><Save size={16} aria-hidden="true" />{pending === "save" ? "Сохраняем..." : "Сохранить черновик"}</Button><Button disabled={!token || pending !== null} onClick={() => void persistDraft(true)}><Send size={16} aria-hidden="true" />{pending === "submit" ? "Отправляем..." : "Отправить заявку"}</Button></div>
    </Card></div> : null}
  </PageLayout></>;
}

function DynamicField({ field, value, files, existingAttachments, users, required, error, onChange, onFilesChange }: { field: ServiceDeskTemplateField; value: unknown; files: File[]; existingAttachments: ServiceDeskAttachment[]; users: Users; required: boolean; error?: string; onChange: (key: string, value: unknown) => void; onFilesChange: (files: File[]) => void }) {
  const label = `${field.label}${required ? " *" : ""}`;
  const common = { name: field.key, id: field.key, "aria-invalid": Boolean(error) };
  const options = getFieldOptions(field);
  if (field.field_type === "file") return <label className="field"><span>{label}</span><FileInput label="Добавить файлы" files={files} onChange={onFilesChange} />{existingAttachments.length ? <ul className="file-selection-list" aria-label="Сохранённые файлы">{existingAttachments.map((attachment) => <li key={attachment.id}><span><strong>{attachment.file_name}</strong><small>{attachment.content_type ?? "Файл"} · {formatSize(attachment.size_bytes)}</small></span></li>)}</ul> : null}<FieldError error={error} /></label>;
  if (field.field_type === "select" || field.field_type === "user") return <label className="field"><span>{label}</span><select {...common} value={String(value ?? "")} onChange={(event) => onChange(field.key, event.target.value)}><option value="">Выберите значение</option>{field.field_type === "user" ? users.map((user) => <option key={user.id} value={user.id}>{user.display_name}</option>) : options.map((option) => <option key={String(option.value)} value={String(option.value)}>{option.label ?? option.value}</option>)}</select><FieldHelp field={field} /><FieldError error={error} /></label>;
  if (field.field_type === "multiselect") return <label className="field"><span>{label}</span><select {...common} multiple value={Array.isArray(value) ? value.map(String) : []} onChange={(event) => onChange(field.key, Array.from(event.target.selectedOptions, (option) => option.value))}>{options.map((option) => <option key={String(option.value)} value={String(option.value)}>{option.label ?? option.value}</option>)}</select><FieldHelp field={field} /><FieldError error={error} /></label>;
  if (field.field_type === "checkbox") return <label className="field"><span className="checkbox-field"><input {...common} type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(field.key, event.target.checked)} />{label}</span><FieldError error={error} /></label>;
  const type = field.field_type === "number" ? "number" : field.field_type === "date" ? "date" : field.field_type === "datetime" ? "datetime-local" : field.field_type === "email" ? "email" : "text";
  return <label className={`field ${field.field_type === "textarea" || field.field_type === "rich_text" ? "field-wide" : ""}`}><span>{label}</span>{field.field_type === "textarea" || field.field_type === "rich_text" ? <textarea {...common} placeholder={field.placeholder ?? undefined} value={String(value ?? "")} onChange={(event) => onChange(field.key, event.target.value)} rows={4} /> : <input {...common} type={type} placeholder={field.placeholder ?? undefined} value={String(value ?? "")} onChange={(event) => onChange(field.key, event.target.value)} />}<FieldHelp field={field} /><FieldError error={error} /></label>;
}

function FieldHelp({ field }: { field: ServiceDeskTemplateField }) { return field.help_text ? <small className="field-help">{field.help_text}</small> : null; }
function FieldError({ error }: { error?: string }) { return error ? <small className="field-error">{error}</small> : null; }
function formatSize(size: number) { return size < 1024 ? `${size} Б` : size < 1024 * 1024 ? `${(size / 1024).toFixed(1)} КБ` : `${(size / 1024 / 1024).toFixed(1)} МБ`; }
