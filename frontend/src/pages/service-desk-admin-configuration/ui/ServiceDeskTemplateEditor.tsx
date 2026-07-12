import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Check, Search as Eye, Pencil, Plus, Save, Trash2 } from "lucide-react";

import type { ServiceDeskService, ServiceDeskTemplateField, ServiceDeskTemplateFieldType } from "../../../entities/service-desk-catalog/model/types";
import { createAdminTemplateField, createAdminTemplateVersion, deleteAdminTemplateField, listAdminServices, listAdminTemplateVersions, previewAdminTemplateVersion, publishAdminTemplateVersion, reorderAdminTemplateFields, updateAdminTemplateField, updateAdminTemplateVersion } from "../../../entities/service-desk-admin/api/serviceDeskAdminConfigApi";
import type { AdminTemplateVersion } from "../../../entities/service-desk-admin/api/serviceDeskAdminConfigApi";
import { getServiceDeskUserOptions } from "../../../entities/service-desk-user/api/serviceDeskUserApi";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";

type Rule = { field?: string; operator?: string; value?: unknown };
type EditorDraft = {
  key: string;
  label: string;
  field_type: ServiceDeskTemplateFieldType;
  is_required: boolean;
  placeholder: string;
  help_text: string;
  options_mode: "static" | "dictionary";
  options_text: string;
  dictionary_code: string;
  min: string;
  max: string;
  min_length: string;
  max_length: string;
  allowed_extensions: string;
  max_files: string;
  condition_kind: "none" | "visibility" | "required";
  condition_field: string;
  condition_operator: string;
  condition_value: string;
  preserved_visibility_rules: Rule | Rule[] | null;
  preserved_required_rules: Rule | Rule[] | null;
};

const fieldTypes: ServiceDeskTemplateFieldType[] = ["text", "textarea", "rich_text", "select", "multiselect", "date", "datetime", "email", "number", "checkbox", "file", "user"];
const operators = ["equals", "not_equals", "in", "not_in", "is_empty", "is_not_empty"];

export function ServiceDeskTemplateEditor() {
  const [services, setServices] = useState<ServiceDeskService[]>([]);
  const [versions, setVersions] = useState<AdminTemplateVersion[]>([]);
  const [serviceId, setServiceId] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [draft, setDraft] = useState<EditorDraft>(() => emptyDraft());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [preview, setPreview] = useState<ServiceDeskTemplateField[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selected = versions.find((version) => version.id === selectedId) ?? null;
  const fieldKeys = useMemo(() => selected?.fields.map((field) => field.key) ?? [], [selected]);

  useEffect(() => { listAdminServices().then(setServices).catch((reason) => setError(errorText(reason, "Не удалось загрузить услуги"))); }, []);
  async function loadVersions(nextService = serviceId) { setServiceId(nextService); setSelectedId(""); setPreview(null); if (!nextService) { setVersions([]); return; } try { const result = await listAdminTemplateVersions(nextService); setVersions(result); setSelectedId(result[0]?.id ?? ""); } catch (reason) { setError(errorText(reason, "Не удалось загрузить версии формы")); } }
  async function addVersion() { if (!serviceId) return; try { const version = await createAdminTemplateVersion(serviceId); setVersions((current) => [version, ...current]); setSelectedId(version.id); } catch (reason) { setError(errorText(reason, "Не удалось создать черновую версию")); } }
  async function saveField() {
    if (!selected || selected.status !== "draft" || !draft.key.trim() || !draft.label.trim()) return;
    try {
      const payload = buildPayload(draft, selected.fields.length);
      if (editingId) {
        const updated = await updateAdminTemplateField(editingId, payload);
        setVersions((current) => current.map((version) => version.id === selected.id ? { ...version, fields: version.fields.map((field) => field.id === updated.id ? updated : field) } : version));
      } else {
        const created = await createAdminTemplateField(selected.id, payload);
        setVersions((current) => current.map((version) => version.id === selected.id ? { ...version, fields: [...version.fields, created] } : version));
      }
      setEditingId(null); setDraft(emptyDraft());
    } catch (reason) { setError(errorText(reason, "Не удалось сохранить поле")); }
  }
  async function removeField(fieldId: string) { if (!selected) return; try { await deleteAdminTemplateField(fieldId); setVersions((current) => current.map((version) => version.id === selected.id ? { ...version, fields: version.fields.filter((field) => field.id !== fieldId) } : version)); } catch (reason) { setError(errorText(reason, "Не удалось удалить поле")); } }
  async function moveField(index: number, delta: number) { if (!selected || selected.status !== "draft") return; const fields = [...selected.fields]; const target = index + delta; if (target < 0 || target >= fields.length) return; [fields[index], fields[target]] = [fields[target], fields[index]]; try { const result = await reorderAdminTemplateFields(selected.id, fields.map((field) => field.id)); setVersions((current) => current.map((version) => version.id === selected.id ? { ...version, fields: result } : version)); } catch (reason) { setError(errorText(reason, "Не удалось изменить порядок полей")); } }
  async function publish() { if (!selected) return; try { await publishAdminTemplateVersion(selected.id); await loadVersions(serviceId); } catch (reason) { setError(errorText(reason, "Не удалось опубликовать форму")); } }
  function startEdit(field: ServiceDeskTemplateField) { setEditingId(field.id); setDraft(fromField(field)); setPreview(null); }
  return <PageLayout title="Шаблоны форм" subtitle="Настройка полей, условий и реальный предпросмотр."><ConfigError error={error} /><div className="admin-config-grid"><Card><Select label="Услуга" value={serviceId} onChange={(event) => void loadVersions(event.target.value)}><option value="">Выберите услугу</option>{services.map((service) => <option key={service.id} value={service.id}>{service.title}</option>)}</Select><Button variant="secondary" onClick={() => void addVersion()} disabled={!serviceId}><Plus size={15} />Новая версия</Button><div className="admin-config-list">{versions.map((version) => <button type="button" className={"admin-config-select " + (version.id === selectedId ? "active" : "")} key={version.id} onClick={() => { setSelectedId(version.id); setPreview(null); }}>{versionLabel(version)}</button>)}</div></Card>{selected ? <Card><div className="service-desk-section-heading"><div><h3>{versionLabel(selected)}</h3><p className="muted">{selected.status === "draft" ? "Черновик можно изменять" : "Опубликованная версия доступна только для просмотра"}</p></div><span className="button-row">{selected.status === "draft" ? <Button onClick={() => void publish()}><Check size={15} />Опубликовать</Button> : null}<Button variant="ghost" onClick={() => void previewAdminTemplateVersion(selected.id).then((result) => setPreview(result.fields)).catch((reason) => setError(errorText(reason, "Не удалось открыть предпросмотр")))}><Eye size={15} />Предпросмотр</Button></span></div>{selected.status === "draft" ? <><VersionSettings version={selected} onSaved={(updated) => setVersions((current) => current.map((item) => item.id === updated.id ? updated : item))} /><FieldEditor draft={draft} fieldKeys={fieldKeys} editingId={editingId} onChange={setDraft} onSave={() => void saveField()} onCancel={() => { setEditingId(null); setDraft(emptyDraft()); }} /></> : null}<div className="admin-config-list">{selected.fields.map((field, index) => <div className="admin-config-row" key={field.id}><span><strong>{field.label}{field.is_required ? " *" : ""}</strong><small>{field.key} · {fieldTypeLabel(field.field_type)}</small></span>{selected.status === "draft" ? <span className="button-row"><Button variant="ghost" onClick={() => startEdit(field)}><Pencil size={15} />Изменить</Button><Button variant="ghost" onClick={() => void moveField(index, -1)} disabled={index === 0}><ArrowUp size={15} /></Button><Button variant="ghost" onClick={() => void moveField(index, 1)} disabled={index === selected.fields.length - 1}><ArrowDown size={15} /></Button><Button variant="ghost" onClick={() => void removeField(field.id)}><Trash2 size={15} /></Button></span> : null}</div>)}</div>{preview ? <TemplatePreview fields={preview} /> : null}</Card> : <Card><p className="muted">Выберите услугу и версию формы.</p></Card>}</div></PageLayout>;
}

function VersionSettings({ version, onSaved }: { version: AdminTemplateVersion; onSaved: (version: AdminTemplateVersion) => void }) {
  const settings = version.system_settings;
  const [defaultTitle, setDefaultTitle] = useState(String(settings.default_title ?? ""));
  const [titleEditable, setTitleEditable] = useState(settings.is_title_editable !== false);
  const [descriptionRequired, setDescriptionRequired] = useState(settings.is_description_required !== false);
  const [helpText, setHelpText] = useState(String(settings.help_text ?? ""));
  const [assigneeId, setAssigneeId] = useState(version.default_assignee_user_id ?? "");
  const [assignees, setAssignees] = useState<Array<{ id: string; display_name: string }>>([]);
  useEffect(() => { getServiceDeskUserOptions("service_desk.be_assignee").then(setAssignees).catch(() => setAssignees([])); }, []);
  async function save() { onSaved(await updateAdminTemplateVersion(version.id, { system_settings: { default_title: defaultTitle || null, is_title_editable: titleEditable, is_description_required: descriptionRequired, help_text: helpText || null }, default_assignee_user_id: assigneeId || null })); }
  return <Card><h3>Настройки версии</h3><div className="admin-config-form-grid"><Input label="Тема по умолчанию" value={defaultTitle} onChange={(event) => setDefaultTitle(event.target.value)} /><label className="checkbox-field"><input type="checkbox" checked={titleEditable} onChange={(event) => setTitleEditable(event.target.checked)} />Тему можно изменять</label><label className="checkbox-field"><input type="checkbox" checked={descriptionRequired} onChange={(event) => setDescriptionRequired(event.target.checked)} />Описание обязательно</label><Input label="Подсказка формы" value={helpText} onChange={(event) => setHelpText(event.target.value)} /><Select label="Исполнитель по умолчанию" value={assigneeId} onChange={(event) => setAssigneeId(event.target.value)}><option value="">Не назначен</option>{assignees.map((user) => <option key={user.id} value={user.id}>{user.display_name}</option>)}</Select><Button onClick={() => void save()}><Save size={15} />Сохранить настройки</Button></div></Card>;
}

function FieldEditor({ draft, fieldKeys, editingId, onChange, onSave, onCancel }: { draft: EditorDraft; fieldKeys: string[]; editingId: string | null; onChange: (draft: EditorDraft) => void; onSave: () => void; onCancel: () => void }) {
  const update = (patch: Partial<EditorDraft>) => onChange({ ...draft, ...patch });
  const isChoice = draft.field_type === "select" || draft.field_type === "multiselect";
  const hasValidation = ["number", "text", "textarea", "rich_text", "email", "file"].includes(draft.field_type);
  return <Card><div className="service-desk-section-heading"><h3>{editingId ? "Изменить поле" : "Добавить поле"}</h3></div><div className="admin-config-form-grid"><Input label="Ключ" value={draft.key} disabled={Boolean(editingId)} onChange={(event) => update({ key: event.target.value })} /><Input label="Название" value={draft.label} onChange={(event) => update({ label: event.target.value })} /><Select label="Тип поля" value={draft.field_type} disabled={Boolean(editingId)} onChange={(event) => update({ field_type: event.target.value as ServiceDeskTemplateFieldType })}>{fieldTypes.map((type) => <option key={type} value={type}>{fieldTypeLabel(type)}</option>)}</Select><label className="checkbox-field"><input type="checkbox" checked={draft.is_required} onChange={(event) => update({ is_required: event.target.checked })} />Обязательное поле</label><Input label="Заполнитель" value={draft.placeholder} onChange={(event) => update({ placeholder: event.target.value })} /><Input label="Подсказка" value={draft.help_text} onChange={(event) => update({ help_text: event.target.value })} />{isChoice ? <><Select label="Источник вариантов" value={draft.options_mode} onChange={(event) => update({ options_mode: event.target.value as "static" | "dictionary" })}><option value="static">Статические варианты</option><option value="dictionary">Справочник</option></Select>{draft.options_mode === "static" ? <Input label="Варианты label=value через запятую" value={draft.options_text} onChange={(event) => update({ options_text: event.target.value })} /> : <Input label="Код справочника" value={draft.dictionary_code} onChange={(event) => update({ dictionary_code: event.target.value, options_text: "" })} />}</> : null}{hasValidation ? <><h4>Ограничения</h4>{draft.field_type === "number" ? <><Input label="Минимум" value={draft.min} onChange={(event) => update({ min: event.target.value })} /><Input label="Максимум" value={draft.max} onChange={(event) => update({ max: event.target.value })} /></> : null}{["text", "textarea", "rich_text", "email"].includes(draft.field_type) ? <><Input label="Минимум символов" value={draft.min_length} onChange={(event) => update({ min_length: event.target.value })} /><Input label="Максимум символов" value={draft.max_length} onChange={(event) => update({ max_length: event.target.value })} /></> : null}{draft.field_type === "file" ? <><Input label="Расширения через запятую" value={draft.allowed_extensions} onChange={(event) => update({ allowed_extensions: event.target.value })} /><Input label="Максимум файлов" value={draft.max_files} onChange={(event) => update({ max_files: event.target.value })} /></> : null}</> : null}<h4>Простое условие</h4><Select label="Тип условия" value={draft.condition_kind} onChange={(event) => update({ condition_kind: event.target.value as EditorDraft["condition_kind"] })}><option value="none">Нет</option><option value="visibility">Показывать при условии</option><option value="required">Обязательно при условии</option></Select>{draft.condition_kind !== "none" ? <><Select label="Поле условия" value={draft.condition_field} onChange={(event) => update({ condition_field: event.target.value })}><option value="">Выберите поле</option>{fieldKeys.filter((key) => key !== draft.key).map((key) => <option key={key} value={key}>{key}</option>)}</Select><Select label="Оператор" value={draft.condition_operator} onChange={(event) => update({ condition_operator: event.target.value })}>{operators.map((operator) => <option key={operator} value={operator}>{operatorLabel(operator)}</option>)}</Select>{!["is_empty", "is_not_empty"].includes(draft.condition_operator) ? <Input label="Значение" value={draft.condition_value} onChange={(event) => update({ condition_value: event.target.value })} /> : null}</> : null}</div><div className="button-row"><Button onClick={onSave} disabled={!draft.key.trim() || !draft.label.trim()}><Save size={15} />Сохранить</Button>{editingId ? <Button variant="ghost" onClick={onCancel}>Отмена</Button> : null}</div>{editingId && (draft.preserved_visibility_rules || draft.preserved_required_rules) ? <p className="muted">У поля несколько условий. Они сохранены; редактор изменяет только остальные свойства.</p> : null}</Card>;
}

function TemplatePreview({ fields }: { fields: ServiceDeskTemplateField[] }) { return <Card><h3>Предпросмотр формы</h3>{fields.map((field) => <div className="field" key={field.id}><span>{field.label}{field.is_required ? " *" : ""}</span>{field.field_type === "select" || field.field_type === "multiselect" ? <select disabled multiple={field.field_type === "multiselect"}><option>Выберите значение</option>{(field.effective_options ?? field.options ?? []).map((option) => <option key={String(option.value)}>{option.label ?? option.value}</option>)}</select> : field.field_type === "textarea" || field.field_type === "rich_text" ? <textarea disabled placeholder={field.placeholder ?? undefined} rows={3} /> : field.field_type === "checkbox" ? <input type="checkbox" disabled /> : <input disabled type={field.field_type === "number" ? "number" : field.field_type === "date" ? "date" : field.field_type === "datetime" ? "datetime-local" : field.field_type === "email" ? "email" : "text"} placeholder={field.placeholder ?? undefined} />}{field.help_text ? <small className="field-help">{field.help_text}</small> : null}</div>)}</Card>; }

function buildPayload(draft: EditorDraft, position: number) {
  const validation: Record<string, unknown> = {};
  if (draft.min) validation.min = Number(draft.min);
  if (draft.max) validation.max = Number(draft.max);
  if (draft.min_length) validation.min_length = Number(draft.min_length);
  if (draft.max_length) validation.max_length = Number(draft.max_length);
  if (draft.allowed_extensions) validation.allowed_extensions = draft.allowed_extensions.split(",").map((item) => item.trim()).filter(Boolean);
  if (draft.max_files) validation.max_files = Number(draft.max_files);
  const rule = draft.condition_kind !== "none" && draft.condition_field ? { field: draft.condition_field, operator: draft.condition_operator, value: draft.condition_value } : null;
  const payload: Record<string, unknown> = { key: draft.key.trim(), label: draft.label.trim(), field_type: draft.field_type, is_required: draft.is_required, position, placeholder: draft.placeholder.trim() || null, help_text: draft.help_text.trim() || null, validation: Object.keys(validation).length ? validation : null };
  if (draft.options_mode === "dictionary" && draft.dictionary_code.trim()) { payload.dictionary_code = draft.dictionary_code.trim(); payload.options = null; } else { payload.dictionary_code = null; payload.options = draft.options_text.split(",").map((item) => item.trim()).filter(Boolean).map((item) => { const parts = item.split("=", 2); return { label: parts[0], value: parts[1] ?? parts[0] }; }); }
  if (draft.preserved_visibility_rules) payload.visibility_rules = draft.preserved_visibility_rules;
  else if (rule && draft.condition_kind === "visibility") payload.visibility_rules = [rule];
  else payload.visibility_rules = null;
  if (draft.preserved_required_rules) payload.required_rules = draft.preserved_required_rules;
  else if (rule && draft.condition_kind === "required") payload.required_rules = [rule];
  else payload.required_rules = null;
  return payload as { key: string; label: string; field_type: ServiceDeskTemplateFieldType; is_required: boolean; position: number };
}
function emptyDraft(): EditorDraft { return { key: "", label: "", field_type: "text", is_required: false, placeholder: "", help_text: "", options_mode: "static", options_text: "", dictionary_code: "", min: "", max: "", min_length: "", max_length: "", allowed_extensions: "", max_files: "", condition_kind: "none", condition_field: "", condition_operator: "equals", condition_value: "", preserved_visibility_rules: null, preserved_required_rules: null }; }
function fromField(field: ServiceDeskTemplateField): EditorDraft { const rule = Array.isArray(field.visibility_rules) ? field.visibility_rules[0] : field.visibility_rules ?? (Array.isArray(field.required_rules) ? field.required_rules[0] : field.required_rules); const condition_kind = field.visibility_rules ? "visibility" : field.required_rules ? "required" : "none"; return { ...emptyDraft(), key: field.key, label: field.label, field_type: field.field_type, is_required: field.is_required, placeholder: field.placeholder ?? "", help_text: field.help_text ?? "", options_mode: field.dictionary_code ? "dictionary" : "static", options_text: (field.options ?? []).map((option) => String(option.label ?? option.value ?? "")).join(", "), dictionary_code: field.dictionary_code ?? "", min: String(field.validation?.min ?? ""), max: String(field.validation?.max ?? ""), min_length: String(field.validation?.min_length ?? ""), max_length: String(field.validation?.max_length ?? ""), allowed_extensions: Array.isArray(field.validation?.allowed_extensions) ? field.validation.allowed_extensions.join(", ") : "", max_files: String(field.validation?.max_files ?? ""), condition_kind, condition_field: typeof rule?.field === "string" ? rule.field : "", condition_operator: typeof rule?.operator === "string" ? rule.operator : "equals", condition_value: typeof rule?.value === "string" ? rule.value : "", preserved_visibility_rules: field.visibility_rules ?? null, preserved_required_rules: field.required_rules ?? null }; }
function versionLabel(version: AdminTemplateVersion) { return "Версия " + version.version + " · " + (version.status === "draft" ? "Черновая версия" : version.status === "published" ? "Опубликовано" : "Архив"); }
function fieldTypeLabel(type: string) { const labels: Record<string, string> = { text: "Текст", textarea: "Большой текст", rich_text: "Форматированный текст", select: "Список", multiselect: "Несколько значений", date: "Дата", datetime: "Дата и время", email: "Email", number: "Число", checkbox: "Флажок", file: "Файл", user: "Пользователь" }; return labels[type] ?? "Поле"; }
function operatorLabel(operator: string) { const labels: Record<string, string> = { equals: "Равно", not_equals: "Не равно", in: "В списке", not_in: "Не в списке", is_empty: "Пусто", is_not_empty: "Заполнено" }; return labels[operator] ?? operator; }
function ConfigError({ error }: { error: string | null }) { return error ? <p className="form-error" role="alert">{error}</p> : null; }
function errorText(reason: unknown, fallback: string) { return reason instanceof Error ? reason.message : fallback; }
