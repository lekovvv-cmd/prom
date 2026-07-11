import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { FileText, Save, Send } from "lucide-react";

import { getServiceDeskService, getServiceDeskServiceForm } from "../../../entities/service-desk-catalog/api/serviceDeskCatalogApi";
import type { ServiceDeskPublishedForm, ServiceDeskService, ServiceDeskTemplateField } from "../../../entities/service-desk-catalog/model/types";
import { createServiceDeskDraft, submitServiceDeskDraft, updateServiceDeskDraft, uploadServiceDeskFieldAttachment } from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import type { ServiceDeskPriority, ServiceDeskTicket } from "../../../entities/service-desk-ticket/model/types";
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

type FormValues = Record<string, unknown>;
type FieldErrors = Record<string, string>;

export function ServiceDeskServiceFormPage() {
  const { serviceId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [service, setService] = useState<ServiceDeskService | null>(null);
  const [form, setForm] = useState<ServiceDeskPublishedForm | null>(null);
  const [values, setValues] = useState<FormValues>({});
  const [filesByField, setFilesByField] = useState<Record<string, File[]>>({});
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
    if (!serviceId) return undefined;
    Promise.all([getServiceDeskService(serviceId), getServiceDeskServiceForm(serviceId)])
      .then(([serviceItem, formData]) => {
        if (!active) return;
        setService(serviceItem);
        setForm(formData);
        const settings = formData.template_version.system_settings;
        setTitle(settings.default_title ?? serviceItem.title);
      })
      .catch((reason: unknown) => { if (active) setError(reason instanceof Error ? reason.message : "Не удалось загрузить услугу"); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [serviceId]);

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
      if (forSubmit && required && isEmpty(field.field_type === "file" ? files : value)) errors[field.key] = "Заполните обязательное поле";
      if (forSubmit && field.field_type === "email" && value && !/^\S+@\S+\.\S+$/.test(String(value))) errors[field.key] = "Укажите корректный email";
      if (forSubmit && field.field_type === "number" && value !== undefined && value !== "" && Number.isNaN(Number(value))) errors[field.key] = "Укажите число";
    });
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function persistDraft(submitAfter: boolean) {
    if (!serviceId || !form) return;
    if (submitAfter && !validate(true)) return;
    if (!token) { navigate("/login"); return; }
    setPending(submitAfter ? "submit" : "save");
    setError(null);
    try {
      const payload = { service_id: serviceId, template_version_id: form.template_version.id, title: title.trim() || service?.title || "Заявка", description, priority, field_values: values };
      let current = draft ? await updateServiceDeskDraft(draft.id, payload) : await createServiceDeskDraft(payload);
      setDraft(current);
      for (const [fieldKey, files] of Object.entries(filesByField)) {
        for (const file of files) await uploadServiceDeskFieldAttachment(current.id, fieldKey, file);
      }
      setFilesByField({});
      if (submitAfter) {
        current = await submitServiceDeskDraft(current.id);
        navigate(`/service-desk/tickets/${current.id}`);
      } else {
        setError("Черновик сохранён. Его можно отправить, когда форма будет готова.");
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

  return (
    <>
      <Header />
      <PageLayout title={service?.title ?? "Услуга Service Desk"} subtitle={service ? `${service.category?.title ?? "Каталог"} · заполните форму заявки` : undefined}>
        {loading ? <Spinner label="Загружаем форму услуги" /> : error && !form ? <Card><p className="form-error" role="alert">{error}</p><Link className="button button-secondary" to="/service-desk">Вернуться в каталог</Link></Card> : form && service ? (
          <div className="service-desk-form-layout">
            <Card className="service-desk-form-card">
              <div className="service-desk-form-intro"><span className="service-desk-eyebrow"><FileText size={14} aria-hidden="true" /> Форма заявки · версия {form.template_version.version}</span><p>{service.description ?? service.short_description}</p>{form.template_version.system_settings.help_text ? <p className="muted">{form.template_version.system_settings.help_text}</p> : null}</div>
              {!token ? <Card><p>Для сохранения заявки войдите в PROM.</p><Link className="button" to="/login">Войти</Link></Card> : null}
              <div className="service-desk-form-grid">
                <Input label="Тема заявки" value={title} disabled={form.template_version.system_settings.is_title_editable === false} onChange={(event) => setTitle(event.target.value)} aria-invalid={Boolean(fieldErrors.title)} />
                <label className="field field-wide"><span>Описание {form.template_version.system_settings.is_description_required !== false ? <sup>*</sup> : null}</span><textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={5} aria-invalid={Boolean(fieldErrors.description)} /></label>
                <Select label="Приоритет" value={priority} onChange={(event) => setPriority(event.target.value as ServiceDeskPriority)}><option value="low">Низкий</option><option value="medium">Средний</option><option value="high">Высокий</option><option value="critical">Критический</option></Select>
                {visibleFields.map((field) => <DynamicField key={field.key} field={field} value={values[field.key]} files={filesByField[field.key] ?? []} error={fieldErrors[field.key]} onChange={updateValue} onFilesChange={(files) => setFilesByField((current) => ({ ...current, [field.key]: files }))} />)}
              </div>
              {error && form ? <p className={error.startsWith("Черновик") ? "success-text" : "form-error"} role="alert">{error}</p> : null}
              <div className="form-actions"><Button variant="secondary" disabled={!token || pending !== null} onClick={() => void persistDraft(false)}><Save size={16} aria-hidden="true" />{pending === "save" ? "Сохраняем..." : "Сохранить черновик"}</Button><Button disabled={!token || pending !== null} onClick={() => void persistDraft(true)}><Send size={16} aria-hidden="true" />{pending === "submit" ? "Отправляем..." : "Отправить заявку"}</Button></div>
            </Card>
          </div>
        ) : null}
      </PageLayout>
    </>
  );
}

function DynamicField({ field, value, files, error, onChange, onFilesChange }: { field: ServiceDeskTemplateField; value: unknown; files: File[]; error?: string; onChange: (key: string, value: unknown) => void; onFilesChange: (files: File[]) => void }) {
  const label = `${field.label}${field.is_required ? " *" : ""}`;
  const common = { name: field.key, id: field.key, "aria-invalid": Boolean(error) };
  return <label className={`field ${field.field_type === "textarea" || field.field_type === "rich_text" ? "field-wide" : ""}`}>
    {field.field_type === "file" ? <><span>{label}</span><FileInput label="Добавить файлы" files={files} onChange={onFilesChange} /><FieldError error={error} /></> : field.field_type === "select" ? <><span>{label}</span><select {...common} value={String(value ?? "")} onChange={(event) => onChange(field.key, event.target.value)}><option value="">Выберите значение</option>{(field.options ?? []).map((option) => <option key={String(option.value)} value={String(option.value)}>{option.label ?? option.value}</option>)}</select><FieldHelp field={field} /><FieldError error={error} /></> : field.field_type === "multiselect" ? <><span>{label}</span><select {...common} multiple value={Array.isArray(value) ? value.map(String) : []} onChange={(event) => onChange(field.key, Array.from(event.target.selectedOptions, (option) => option.value))}>{(field.options ?? []).map((option) => <option key={String(option.value)} value={String(option.value)}>{option.label ?? option.value}</option>)}</select><FieldHelp field={field} /><FieldError error={error} /></> : field.field_type === "checkbox" ? <span className="checkbox-field"><input {...common} type="checkbox" checked={Boolean(value)} onChange={(event) => onChange(field.key, event.target.checked)} />{label}</span> : field.field_type === "textarea" || field.field_type === "rich_text" ? <><span>{label}</span><textarea {...common} placeholder={field.placeholder ?? undefined} value={String(value ?? "")} onChange={(event) => onChange(field.key, event.target.value)} rows={4} /><FieldHelp field={field} /><FieldError error={error} /></> : <><span>{label}</span><input {...common} type={field.field_type === "number" ? "number" : field.field_type === "date" ? "date" : field.field_type === "datetime" ? "datetime-local" : field.field_type === "email" ? "email" : "text"} placeholder={field.placeholder ?? undefined} value={String(value ?? "")} onChange={(event) => onChange(field.key, event.target.value)} /><FieldHelp field={field} /><FieldError error={error} /></>}
  </label>;
}

function FieldHelp({ field }: { field: ServiceDeskTemplateField }) { return field.help_text ? <small className="field-help">{field.help_text}</small> : null; }
function FieldError({ error }: { error?: string }) { return error ? <small className="field-error">{error}</small> : null; }
function isEmpty(value: unknown) { return value === undefined || value === null || value === "" || (Array.isArray(value) && value.length === 0); }
function matchesRules(rules: Record<string, unknown> | null | undefined, values: FormValues, fallback: boolean) {
  if (!rules) return fallback;
  const field = typeof rules.field === "string" ? rules.field : "";
  const operator = rules.operator ?? "equals";
  const actual = values[field];
  const expected = rules.value;
  if (operator === "equals") return actual === expected;
  if (operator === "not_equals") return actual !== expected;
  if (operator === "in") return Array.isArray(expected) && expected.includes(actual);
  if (operator === "not_in") return Array.isArray(expected) && !expected.includes(actual);
  if (operator === "is_empty") return isEmpty(actual);
  if (operator === "is_not_empty") return !isEmpty(actual);
  return false;
}
