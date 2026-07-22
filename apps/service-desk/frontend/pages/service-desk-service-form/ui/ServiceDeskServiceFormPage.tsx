import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { FileText, Save, Send } from "lucide-react";

import {
  getServiceDeskService,
  getServiceDeskServiceForm,
} from "../../../entities/service-desk-catalog/api/serviceDeskCatalogApi";
import type {
  ServiceDeskPublishedForm,
  ServiceDeskService,
  ServiceDeskTemplateField,
} from "../../../entities/service-desk-catalog/model/types";
import {
  getFieldOptions,
  isEmpty,
  matchesRules,
  type FormValues,
} from "../../../entities/service-desk-catalog/model/rules";
import { getServiceDeskUserOptions } from "../../../entities/service-desk-user/api/serviceDeskUserApi";
import {
  deleteServiceDeskAttachment,
  downloadServiceDeskAttachment,
  getServiceDeskTicket,
  getServiceDeskTicketForm,
  listServiceDeskFieldAttachments,
  uploadServiceDeskFieldAttachment,
  createServiceDeskDraft,
  submitServiceDeskDraft,
  updateServiceDeskDraft,
} from "../../../entities/service-desk-ticket/api/serviceDeskTicketApi";
import type {
  ServiceDeskAttachment,
  ServiceDeskPriority,
  ServiceDeskTicket,
} from "../../../entities/service-desk-ticket/model/types";
import { ApiError } from "@prom/api-client";
import { FileInput } from "@prom/ui/FileInput";
import { useAuth } from "@prom/auth";
import { Button } from "@prom/ui/Button";
import { Card } from "@prom/ui/Card";
import { Input } from "@prom/ui/Input";
import { PageLayout } from "@prom/ui/PageLayout";
import { Select } from "@prom/ui/Select";
import { Spinner } from "@prom/ui/Spinner";
import { Header } from "@prom/layout";
import { ServiceDeskDynamicFields } from "../../../widgets/service-desk-dynamic-fields/ui/ServiceDeskDynamicFields";

type FieldErrors = Record<string, string>;
type Users = Array<{ id: string; display_name: string }>;

export function ServiceDeskServiceFormPage() {
  const { serviceId, ticketId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [service, setService] = useState<ServiceDeskService | null>(null);
  const [form, setForm] = useState<ServiceDeskPublishedForm | null>(null);
  const [values, setValues] = useState<FormValues>({});
  const [filesByField, setFilesByField] = useState<Record<string, File[]>>({});
  const [existingByField, setExistingByField] = useState<
    Record<string, ServiceDeskAttachment[]>
  >({});
  const [users, setUsers] = useState<Users>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<ServiceDeskPriority>("medium");
  const [draft, setDraft] = useState<ServiceDeskTicket | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<"save" | "submit" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const formElementRef = useRef<HTMLFormElement | null>(null);
  const mutationLockRef = useRef(false);

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const ticket = ticketId ? await getServiceDeskTicket(ticketId) : null;
        const resolvedServiceId = ticket?.service_id ?? serviceId;
        if (!resolvedServiceId) return;
        const [serviceItem, formData] = await Promise.all([
          getServiceDeskService(resolvedServiceId),
          ticketId
            ? getServiceDeskTicketForm(ticketId)
            : getServiceDeskServiceForm(resolvedServiceId),
        ]);
        if (!active) return;
        setService(serviceItem);
        setForm(formData);
        const settings = formData.template_version.system_settings;
        setTitle(ticket?.title ?? settings.default_title ?? serviceItem.title);
        setDescription(ticket?.description ?? "");
        setPriority(ticket?.priority ?? "medium");
        setValues(
          ticket ? ticket.field_values : fieldDefaults(formData.fields),
        );
        setDraft(ticket);
        if (ticketId && ticket) {
          const fileFields = formData.fields.filter(
            (field) => field.field_type === "file",
          );
          const entries = await Promise.all(
            fileFields.map(
              async (field) =>
                [
                  field.key,
                  await listServiceDeskFieldAttachments(ticket.id, field.key),
                ] as const,
            ),
          );
          if (active) setExistingByField(Object.fromEntries(entries));
        }
        if (formData.fields.some((field) => field.field_type === "user")) {
          const options = await getServiceDeskUserOptions();
          if (active) setUsers(options);
        }
      } catch (reason: unknown) {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Не удалось загрузить форму услуги",
          );
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [serviceId, ticketId]);

  const visibleFields = useMemo(
    () =>
      (form?.fields ?? [])
        .filter((field) => matchesRules(field.visibility_rules, values, true))
        .sort((left, right) => left.position - right.position),
    [form, values],
  );

  const updateValue = useCallback((key: string, value: unknown) => {
    setValues((current) => ({ ...current, [key]: value }));
    setFieldErrors((current) => {
      const next = { ...current };
      delete next[key];
      return next;
    });
  }, []);

  function validate(forSubmit: boolean) {
    const errors: FieldErrors = {};
    if (forSubmit && title.trim().length < 2)
      errors.title = "Укажите тему заявки";
    if (
      forSubmit &&
      form?.template_version.system_settings.is_description_required !==
        false &&
      !description.trim()
    )
      errors.description = "Заполните описание заявки";
    visibleFields.forEach((field) => {
      const required =
        field.is_required || matchesRules(field.required_rules, values, false);
      const value = values[field.key];
      const files = filesByField[field.key] ?? [];
      const existing = existingByField[field.key] ?? [];
      if (
        forSubmit &&
        required &&
        isEmpty(field.field_type === "file" ? [...files, ...existing] : value)
      )
        errors[field.key] = "Заполните обязательное поле";
      if (
        forSubmit &&
        field.field_type === "email" &&
        value &&
        !/^\S+@\S+\.\S+$/.test(String(value))
      )
        errors[field.key] = "Укажите корректный email";
      if (
        forSubmit &&
        field.field_type === "number" &&
        value !== undefined &&
        value !== "" &&
        Number.isNaN(Number(value))
      )
        errors[field.key] = "Укажите число";
    });
    setFieldErrors(errors);
    const valid = Object.keys(errors).length === 0;
    if (!valid) {
      setError("Заполните обязательные поля");
      window.requestAnimationFrame(() => {
        const firstInvalid = formElementRef.current?.querySelector<HTMLElement>(
          '[aria-invalid="true"]',
        );
        firstInvalid?.scrollIntoView({ behavior: "smooth", block: "center" });
        firstInvalid?.focus({ preventScroll: true });
      });
    }
    return valid;
  }

  async function persistDraft(submitAfter: boolean) {
    if (!form || !service || mutationLockRef.current) return;
    if (submitAfter && !validate(true)) return;
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    mutationLockRef.current = true;
    setPending(submitAfter ? "submit" : "save");
    setError(null);
    try {
      const common = {
        title: title.trim() || service.title,
        description,
        priority,
        field_values: values,
      };
      let current: ServiceDeskTicket;
      if (draft) current = await updateServiceDeskDraft(draft.id, common);
      else
        current = await createServiceDeskDraft({
          service_id: service.id,
          template_version_id: form.template_version.id,
          ...common,
        });
      setDraft(current);
      for (const [fieldKey, files] of Object.entries(filesByField)) {
        for (const file of files) {
          try {
            const uploaded = await uploadServiceDeskFieldAttachment(
              current.id,
              fieldKey,
              file,
            );
            setExistingByField((existing) => ({
              ...existing,
              [fieldKey]: [...(existing[fieldKey] ?? []), uploaded],
            }));
          } catch (reason: unknown) {
            setFieldErrors((currentErrors) => ({
              ...currentErrors,
              [fieldKey]:
                reason instanceof Error
                  ? reason.message
                  : "Не удалось загрузить файл",
            }));
            throw reason;
          }
        }
      }
      setFilesByField({});
      if (submitAfter) {
        current = await submitServiceDeskDraft(current.id);
        navigate(`/service-desk/tickets/${current.id}`);
      } else {
        setError(
          "Черновик сохранён. Его можно отправить позже из раздела «Мои заявки».",
        );
      }
    } catch (reason: unknown) {
      if (
        reason instanceof ApiError &&
        reason.details &&
        typeof reason.details === "object" &&
        "detail" in reason.details
      ) {
        const detail = (reason.details as { detail?: unknown }).detail;
        if (
          detail &&
          typeof detail === "object" &&
          "errors" in detail &&
          Array.isArray((detail as { errors?: unknown }).errors)
        ) {
          const next: FieldErrors = {};
          for (const item of (
            detail as {
              errors: Array<{ field_key?: unknown; message?: unknown }>;
            }
          ).errors)
            if (typeof item.field_key === "string")
              next[item.field_key] =
                typeof item.message === "string"
                  ? item.message
                  : "Проверьте поле";
          setFieldErrors(next);
        }
      }
      if (reason instanceof ApiError && reason.status === 403) {
        setError(
          "У вашей учётной записи нет доступа к созданию заявок Service Desk.",
        );
      } else if (reason instanceof ApiError && reason.status === 409) {
        setError(
          "Черновик уже изменён или отправлен. Обновите страницу и повторите действие.",
        );
      } else if (reason instanceof ApiError && reason.status === 422) {
        setError("Заполните обязательные поля");
      } else {
        setError(
          submitAfter
            ? "Не удалось отправить заявку. Проверьте соединение и повторите попытку."
            : "Не удалось сохранить черновик. Проверьте соединение и повторите попытку.",
        );
      }
    } finally {
      mutationLockRef.current = false;
      setPending(null);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void persistDraft(true);
  }

  return (
    <>
      <Header />
      <PageLayout
        title={service?.title ?? "Услуга Service Desk"}
        subtitle={
          service
            ? `${service.category?.title ?? "Каталог"} · заполните форму заявки`
            : undefined
        }
      >
        {loading ? (
          <Spinner label="Загружаем форму услуги" />
        ) : error && !form ? (
          <Card>
            <p className="form-error" role="alert">
              {error}
            </p>
            <Link className="button button-secondary" to="/service-desk">
              Вернуться в каталог
            </Link>
          </Card>
        ) : form && service ? (
          <div className="service-desk-form-layout">
            <Card className="service-desk-form-card">
              <form ref={formElementRef} onSubmit={handleSubmit} noValidate>
                <div className="service-desk-form-intro">
                  <span className="service-desk-eyebrow">
                    <FileText size={14} aria-hidden="true" /> Форма заявки ·
                    версия {form.template_version.version}
                  </span>
                  <p>{service.description ?? service.short_description}</p>
                  {form.template_version.system_settings.help_text ? (
                    <p className="muted">
                      {form.template_version.system_settings.help_text}
                    </p>
                  ) : null}
                </div>
                {!isAuthenticated ? (
                  <Card>
                    <p>Для сохранения заявки войдите в PROM.</p>
                    <Link className="button" to="/login">
                      Войти
                    </Link>
                  </Card>
                ) : null}
                <div className="service-desk-form-grid">
                  <div>
                    <Input
                      id="ticket-title"
                      label="Тема заявки"
                      value={title}
                      disabled={
                        form.template_version.system_settings
                          .is_title_editable === false
                      }
                      onChange={(event) => {
                        setTitle(event.target.value);
                        setFieldErrors((current) => {
                          const next = { ...current };
                          delete next.title;
                          return next;
                        });
                      }}
                      aria-invalid={Boolean(fieldErrors.title)}
                      aria-describedby={
                        fieldErrors.title ? "ticket-title-error" : undefined
                      }
                    />
                    <FieldError
                      id="ticket-title-error"
                      error={fieldErrors.title}
                    />
                  </div>
                  <label
                    className="field field-wide"
                    htmlFor="ticket-description"
                  >
                    <span>
                      Описание{" "}
                      {form.template_version.system_settings
                        .is_description_required !== false ? (
                        <sup>*</sup>
                      ) : null}
                    </span>
                    <textarea
                      id="ticket-description"
                      value={description}
                      onChange={(event) => {
                        setDescription(event.target.value);
                        setFieldErrors((current) => {
                          const next = { ...current };
                          delete next.description;
                          return next;
                        });
                      }}
                      rows={5}
                      aria-invalid={Boolean(fieldErrors.description)}
                      aria-describedby={
                        fieldErrors.description
                          ? "ticket-description-error"
                          : undefined
                      }
                    />
                    <FieldError
                      id="ticket-description-error"
                      error={fieldErrors.description}
                    />
                  </label>
                  <Select
                    label="Приоритет"
                    value={priority}
                    onChange={(event) =>
                      setPriority(event.target.value as ServiceDeskPriority)
                    }
                  >
                    <option value="low">Низкий</option>
                    <option value="medium">Средний</option>
                    <option value="high">Высокий</option>
                    <option value="critical">Критический</option>
                  </Select>
                  <ServiceDeskDynamicFields
                    fields={form.fields}
                    values={values}
                    users={users}
                    errors={fieldErrors}
                    onChange={updateValue}
                    renderFileField={(field, required, fieldError) => (
                      <DynamicField
                        ticketId={draft?.id ?? ticketId}
                        field={field}
                        value={values[field.key]}
                        files={filesByField[field.key] ?? []}
                        existingAttachments={existingByField[field.key] ?? []}
                        users={users}
                        required={required}
                        error={fieldError}
                        onChange={updateValue}
                        onFilesChange={(files) =>
                          setFilesByField((current) => ({
                            ...current,
                            [field.key]: files,
                          }))
                        }
                        onAttachmentRemoved={(attachmentId) =>
                          setExistingByField((current) => ({
                            ...current,
                            [field.key]: (current[field.key] ?? []).filter(
                              (item) => item.id !== attachmentId,
                            ),
                          }))
                        }
                      />
                    )}
                  />
                </div>
                {error && form ? (
                  <p
                    className={
                      error.startsWith("Черновик")
                        ? "success-text"
                        : "form-error"
                    }
                    role="alert"
                  >
                    {error}
                  </p>
                ) : null}
                <div className="form-actions">
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={!isAuthenticated || pending !== null}
                    onClick={() => void persistDraft(false)}
                  >
                    <Save size={16} aria-hidden="true" />
                    {pending === "save" ? "Сохраняем..." : "Сохранить черновик"}
                  </Button>
                  <Button
                    type="submit"
                    disabled={!isAuthenticated || pending !== null}
                  >
                    <Send size={16} aria-hidden="true" />
                    {pending === "submit"
                      ? "Отправляем..."
                      : "Отправить заявку"}
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        ) : null}
      </PageLayout>
    </>
  );
}

function DynamicField({
  ticketId,
  field,
  value,
  files,
  existingAttachments,
  users,
  required,
  error,
  onChange,
  onFilesChange,
  onAttachmentRemoved,
}: {
  ticketId?: string;
  field: ServiceDeskTemplateField;
  value: unknown;
  files: File[];
  existingAttachments: ServiceDeskAttachment[];
  users: Users;
  required: boolean;
  error?: string;
  onChange: (key: string, value: unknown) => void;
  onFilesChange: (files: File[]) => void;
  onAttachmentRemoved: (attachmentId: string) => void;
}) {
  const label = `${field.label}${required ? " *" : ""}`;
  const errorId = `${field.key}-error`;
  const common = {
    name: field.key,
    id: field.key,
    "aria-invalid": Boolean(error),
    "aria-describedby": error ? errorId : undefined,
  };
  const options = getFieldOptions(field);
  if (field.field_type === "file")
    return (
      <label className="field">
        <span>{label}</span>
        <FileInput
          id={field.key}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          label="Добавить файлы"
          files={files}
          onChange={onFilesChange}
        />
        {existingAttachments.length ? (
          <ul className="file-selection-list" aria-label="Сохранённые файлы">
            {existingAttachments.map((attachment) => (
              <li key={attachment.id}>
                <span>
                  <strong>{attachment.file_name}</strong>
                  <small>
                    {attachment.content_type ?? "Файл"} ·{" "}
                    {formatSize(attachment.size_bytes)}
                  </small>
                </span>
                {ticketId ? (
                  <span className="table-actions">
                    <button
                      type="button"
                      className="button button-secondary"
                      onClick={() =>
                        void downloadExistingAttachment(ticketId, attachment)
                      }
                    >
                      ↓ Скачать
                    </button>
                    <button
                      type="button"
                      className="button button-secondary"
                      onClick={() =>
                        void deleteServiceDeskAttachment(
                          ticketId,
                          attachment.id,
                        ).then(() => onAttachmentRemoved(attachment.id))
                      }
                    >
                      Удалить
                    </button>
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}
        <FieldError id={errorId} error={error} />
      </label>
    );
  if (field.field_type === "select" || field.field_type === "user")
    return (
      <label className="field">
        <span>{label}</span>
        <select
          {...common}
          value={String(value ?? "")}
          onChange={(event) => onChange(field.key, event.target.value)}
        >
          <option value="">Выберите значение</option>
          {field.field_type === "user"
            ? users.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.display_name}
                </option>
              ))
            : options.map((option) => (
                <option key={String(option.value)} value={String(option.value)}>
                  {option.label ?? option.value}
                </option>
              ))}
        </select>
        <FieldHelp field={field} />
        <FieldError error={error} />
      </label>
    );
  if (field.field_type === "multiselect")
    return (
      <label className="field">
        <span>{label}</span>
        <select
          {...common}
          multiple
          value={Array.isArray(value) ? value.map(String) : []}
          onChange={(event) =>
            onChange(
              field.key,
              Array.from(
                event.target.selectedOptions,
                (option) => option.value,
              ),
            )
          }
        >
          {options.map((option) => (
            <option key={String(option.value)} value={String(option.value)}>
              {option.label ?? option.value}
            </option>
          ))}
        </select>
        <FieldHelp field={field} />
        <FieldError error={error} />
      </label>
    );
  if (field.field_type === "checkbox")
    return (
      <label className="field">
        <span className="checkbox-field">
          <input
            {...common}
            type="checkbox"
            checked={Boolean(value)}
            onChange={(event) => onChange(field.key, event.target.checked)}
          />
          {label}
        </span>
        <FieldError error={error} />
      </label>
    );
  const type =
    field.field_type === "number"
      ? "number"
      : field.field_type === "date"
        ? "date"
        : field.field_type === "datetime"
          ? "datetime-local"
          : field.field_type === "email"
            ? "email"
            : "text";
  return (
    <label
      className={`field ${field.field_type === "textarea" || field.field_type === "rich_text" ? "field-wide" : ""}`}
    >
      <span>{label}</span>
      {field.field_type === "textarea" || field.field_type === "rich_text" ? (
        <textarea
          {...common}
          placeholder={field.placeholder ?? undefined}
          value={String(value ?? "")}
          onChange={(event) => onChange(field.key, event.target.value)}
          rows={4}
        />
      ) : (
        <input
          {...common}
          type={type}
          placeholder={field.placeholder ?? undefined}
          value={String(value ?? "")}
          onChange={(event) => onChange(field.key, event.target.value)}
        />
      )}
      <FieldHelp field={field} />
      <FieldError error={error} />
    </label>
  );
}

function FieldHelp({ field }: { field: ServiceDeskTemplateField }) {
  return field.help_text ? (
    <small className="field-help">{field.help_text}</small>
  ) : null;
}
function FieldError({ error, id }: { error?: string; id?: string }) {
  return error ? (
    <small id={id} className="field-error">
      {error}
    </small>
  ) : null;
}
function fieldDefaults(fields: ServiceDeskTemplateField[]): FormValues {
  return Object.fromEntries(
    fields.flatMap((field) => {
      const value = field.validation?.default_value;
      if (value !== undefined) return [[field.key, value]];
      return field.field_type === "checkbox" ? [[field.key, false]] : [];
    }),
  );
}
function formatSize(size: number) {
  return size < 1024
    ? `${size} Б`
    : size < 1024 * 1024
      ? `${(size / 1024).toFixed(1)} КБ`
      : `${(size / 1024 / 1024).toFixed(1)} МБ`;
}
async function downloadExistingAttachment(
  ticketId: string,
  attachment: ServiceDeskAttachment,
) {
  const blob = await downloadServiceDeskAttachment(ticketId, attachment.id);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = attachment.file_name;
  link.click();
  URL.revokeObjectURL(url);
}
