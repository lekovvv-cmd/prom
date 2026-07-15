import { useEffect, useMemo, useState } from "react";
import { ArrowDown, ArrowUp, Check, Search as Eye, Pencil, Plus, Save, Trash2 } from "lucide-react";

import type { ServiceDeskService, ServiceDeskTemplateField, ServiceDeskTemplateFieldType } from "../../../entities/service-desk-catalog/model/types";
import { createAdminTemplateField, createAdminTemplateVersion, deleteAdminTemplateField, listAdminDictionaries, listAdminServices, listAdminTemplateVersions, previewAdminTemplateVersion, publishAdminTemplateVersion, reorderAdminTemplateFields, updateAdminTemplateField, updateAdminTemplateVersion } from "../../../entities/service-desk-admin/api/serviceDeskAdminConfigApi";
import type { AdminDictionary, AdminTemplateVersion } from "../../../entities/service-desk-admin/api/serviceDeskAdminConfigApi";
import { getServiceDeskUserOptions } from "../../../entities/service-desk-user/api/serviceDeskUserApi";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { createSystemSlug } from "../../../shared/lib/createSystemSlug";
import { ServiceDeskDynamicFields } from "../../../widgets/service-desk-dynamic-fields/ui/ServiceDeskDynamicFields";

type Rule = { field?: string; operator?: string; value?: unknown };
type FieldReference = { key: string; label: string; fieldType: ServiceDeskTemplateFieldType };
type RuleKind = "visibility" | "required";
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
  visibility_rules: Rule[];
  required_rules: Rule[];
};

const fieldTypes: ServiceDeskTemplateFieldType[] = ["text", "textarea", "rich_text", "select", "multiselect", "date", "time", "datetime", "email", "number", "checkbox", "file", "user"];
const operators = ["equals", "not_equals", "in", "not_in", "is_empty", "is_not_empty"];

export function ServiceDeskTemplateEditor() {
  const [services, setServices] = useState<ServiceDeskService[]>([]);
  const [dictionaries, setDictionaries] = useState<AdminDictionary[]>([]);
  const [versions, setVersions] = useState<AdminTemplateVersion[]>([]);
  const [serviceId, setServiceId] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [draft, setDraft] = useState<EditorDraft>(() => emptyDraft());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [preview, setPreview] = useState<ServiceDeskTemplateField[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selected = versions.find((version) => version.id === selectedId) ?? null;
  const fieldReferences = useMemo<FieldReference[]>(() => selected?.fields.map((field) => ({ key: field.key, label: field.label, fieldType: field.field_type })) ?? [], [selected]);

  useEffect(() => {
    listAdminServices().then(setServices).catch((reason) => setError(errorText(reason, "Не удалось загрузить услуги")));
    listAdminDictionaries().then(setDictionaries).catch(() => setDictionaries([]));
  }, []);

  async function loadVersions(nextService = serviceId) {
    setServiceId(nextService);
    setSelectedId("");
    setPreview(null);
    setEditingId(null);
    setDraft(emptyDraft());
    if (!nextService) {
      setVersions([]);
      return;
    }
    try {
      const result = await listAdminTemplateVersions(nextService);
      setVersions(result);
      setSelectedId(result[0]?.id ?? "");
    } catch (reason) {
      setError(errorText(reason, "Не удалось загрузить версии формы"));
    }
  }

  async function addVersion() {
    if (!serviceId) return;
    try {
      const version = await createAdminTemplateVersion(serviceId);
      setVersions((current) => [version, ...current]);
      setSelectedId(version.id);
      setEditingId(null);
      setDraft(emptyDraft());
    } catch (reason) {
      setError(errorText(reason, "Не удалось создать черновую версию"));
    }
  }

  async function saveField() {
    const fieldKey = draft.key.trim() || createSystemSlug(draft.label);
    if (!selected || selected.status !== "draft" || !fieldKey || !draft.label.trim()) return;
    try {
      const payload = buildPayload({ ...draft, key: fieldKey }, selected.fields.length);
      if (editingId) {
        const updated = await updateAdminTemplateField(editingId, payload);
        setVersions((current) => current.map((version) => version.id === selected.id ? { ...version, fields: version.fields.map((field) => field.id === updated.id ? updated : field) } : version));
      } else {
        const created = await createAdminTemplateField(selected.id, payload);
        setVersions((current) => current.map((version) => version.id === selected.id ? { ...version, fields: [...version.fields, created] } : version));
      }
      setEditingId(null);
      setDraft(emptyDraft());
    } catch (reason) {
      setError(errorText(reason, "Не удалось сохранить поле"));
    }
  }

  async function removeField(fieldId: string) {
    if (!selected) return;
    try {
      await deleteAdminTemplateField(fieldId);
      setVersions((current) => current.map((version) => version.id === selected.id ? { ...version, fields: version.fields.filter((field) => field.id !== fieldId) } : version));
    } catch (reason) {
      setError(errorText(reason, "Не удалось удалить поле"));
    }
  }

  async function moveField(index: number, delta: number) {
    if (!selected || selected.status !== "draft") return;
    const fields = [...selected.fields];
    const target = index + delta;
    if (target < 0 || target >= fields.length) return;
    [fields[index], fields[target]] = [fields[target], fields[index]];
    try {
      const result = await reorderAdminTemplateFields(selected.id, fields.map((field) => field.id));
      setVersions((current) => current.map((version) => version.id === selected.id ? { ...version, fields: result } : version));
    } catch (reason) {
      setError(errorText(reason, "Не удалось изменить порядок полей"));
    }
  }

  async function publish() {
    if (!selected) return;
    try {
      await publishAdminTemplateVersion(selected.id);
      await loadVersions(serviceId);
    } catch (reason) {
      setError(errorText(reason, "Не удалось опубликовать форму"));
    }
  }

  function startEdit(field: ServiceDeskTemplateField) {
    setEditingId(field.id);
    setDraft(fromField(field));
    setPreview(null);
  }

  return (
    <PageLayout title="Шаблоны форм" subtitle="Создавайте форму заявки по шагам: название поля, тип ответа и правила — только если они нужны.">
      <ConfigError error={error} />
      <div className="admin-config-grid template-builder-grid">
        <Card className="template-version-sidebar">
          <div className="template-sidebar-heading">
            <h3>1. Выберите услугу</h3>
            <p className="muted">У каждой услуги своя форма заявки и история её версий.</p>
          </div>
          <Select label="Услуга" value={serviceId} onChange={(event) => void loadVersions(event.target.value)}>
            <option value="">Выберите услугу</option>
            {services.map((service) => <option key={service.id} value={service.id}>{service.title}</option>)}
          </Select>
          <div className="template-version-actions">
            <Button variant="secondary" onClick={() => void addVersion()} disabled={!serviceId}><Plus size={15} />Создать новую версию</Button>
            <small className="field-help">Новая версия — отдельный черновик. Добавьте в него нужные поля: опубликованные заявки не изменятся.</small>
          </div>
          {serviceId && !versions.length ? <p className="template-empty-copy">У этой услуги ещё нет форм. Создайте первую версию, чтобы добавить поля.</p> : null}
          {versions.length ? <div className="admin-config-list template-version-list" aria-label="Версии формы">
            {versions.map((version) => <button type="button" className={`admin-config-select template-version-select ${version.id === selectedId ? "active" : ""}`} key={version.id} onClick={() => { setSelectedId(version.id); setPreview(null); setEditingId(null); setDraft(emptyDraft()); }}>
              <strong>Версия {version.version}</strong>
              <small>{versionStatusLabel(version.status)}</small>
            </button>)}
          </div> : null}
        </Card>
        {selected ? <Card className="template-editor-surface">
          <div className="template-editor-header">
            <div>
              <span className={`template-version-badge is-${selected.status}`}>{versionStatusLabel(selected.status)}</span>
              <h3>Форма для услуги</h3>
              <p className="muted">{selected.status === "draft" ? "Настройте поля, затем опубликуйте версию. В заявках, созданных ранее, форма останется прежней." : "Эта версия уже используется в заявках и доступна только для просмотра."}</p>
            </div>
            <span className="button-row">
              {selected.status === "draft" ? <Button onClick={() => void publish()}><Check size={15} />Опубликовать версию</Button> : null}
              <Button variant="ghost" onClick={() => void previewAdminTemplateVersion(selected.id).then((result) => setPreview(result.fields)).catch((reason) => setError(errorText(reason, "Не удалось открыть предпросмотр")))}><Eye size={15} />Открыть предпросмотр</Button>
            </span>
          </div>
          {selected.status === "draft" ? <>
            <VersionSettings version={selected} onSaved={(updated) => setVersions((current) => current.map((item) => item.id === updated.id ? updated : item))} />
            <FieldEditor draft={draft} fields={fieldReferences} dictionaries={dictionaries} editingId={editingId} onChange={setDraft} onSave={() => void saveField()} onCancel={() => { setEditingId(null); setDraft(emptyDraft()); }} />
          </> : null}
          <section className="template-fields-section" aria-labelledby="template-fields-heading">
            <div className="service-desk-section-heading">
              <div>
                <h3 id="template-fields-heading">Поля формы <span className="template-fields-count">{selected.fields.length}</span></h3>
                <p className="muted">Именно в таком порядке пользователь увидит поля при создании заявки.</p>
              </div>
            </div>
            {!selected.fields.length ? <p className="template-empty-copy">Добавьте первое поле выше. Например, «Тема обращения» или «Дата занятия».</p> : null}
            <div className="admin-config-list">
              {selected.fields.map((field, index) => <div className="admin-config-row template-field-row" key={field.id}>
                <span>
                  <strong>{field.label}{field.is_required ? " *" : ""}</strong>
                  <small>{fieldTypeLabel(field.field_type)}</small>
                </span>
                {selected.status === "draft" ? <span className="button-row">
                  <Button variant="ghost" onClick={() => startEdit(field)}><Pencil size={15} />Изменить</Button>
                  <Button variant="ghost" aria-label={`Поднять поле «${field.label}»`} onClick={() => void moveField(index, -1)} disabled={index === 0}><ArrowUp size={15} /></Button>
                  <Button variant="ghost" aria-label={`Опустить поле «${field.label}»`} onClick={() => void moveField(index, 1)} disabled={index === selected.fields.length - 1}><ArrowDown size={15} /></Button>
                  <Button variant="ghost" aria-label={`Удалить поле «${field.label}»`} onClick={() => void removeField(field.id)}><Trash2 size={15} /></Button>
                </span> : null}
              </div>)}
            </div>
          </section>
          {preview ? <TemplatePreview fields={preview} /> : null}
        </Card> : <Card className="template-empty-state"><h3>Начните с услуги</h3><p className="muted">Слева выберите услугу и версию формы. Для новой услуги сначала создайте черновую версию.</p></Card>}
      </div>
    </PageLayout>
  );
}

function VersionSettings({ version, onSaved }: { version: AdminTemplateVersion; onSaved: (version: AdminTemplateVersion) => void }) {
  const settings = version.system_settings;
  const [defaultTitle, setDefaultTitle] = useState(String(settings.default_title ?? ""));
  const [titleEditable, setTitleEditable] = useState(settings.is_title_editable !== false);
  const [descriptionRequired, setDescriptionRequired] = useState(settings.is_description_required !== false);
  const [helpText, setHelpText] = useState(String(settings.help_text ?? ""));
  const [assigneeId, setAssigneeId] = useState(version.default_assignee_user_id ?? "");
  const [assignees, setAssignees] = useState<Array<{ id: string; display_name: string }>>([]);

  useEffect(() => {
    getServiceDeskUserOptions("service_desk.be_assignee").then(setAssignees).catch(() => setAssignees([]));
  }, []);

  async function save() {
    onSaved(await updateAdminTemplateVersion(version.id, {
      system_settings: { default_title: defaultTitle || null, is_title_editable: titleEditable, is_description_required: descriptionRequired, help_text: helpText || null },
      default_assignee_user_id: assigneeId || null
    }));
  }

  return <Card className="template-version-settings">
    <div className="template-section-title"><span className="template-step-number">Общее</span><div><h3>Настройки всей формы</h3><p className="muted">Эти параметры относятся ко всей заявке, а не к отдельному полю.</p></div></div>
    <div className="template-step-grid">
      <div className="template-control-with-help"><Input label="Тема заявки по умолчанию" value={defaultTitle} onChange={(event) => setDefaultTitle(event.target.value)} /><small className="field-help">Подставится в новую заявку, если пользователь её не изменит.</small></div>
      <div className="template-control-with-help"><Input label="Подсказка в начале формы" value={helpText} onChange={(event) => setHelpText(event.target.value)} /><small className="field-help">Коротко объясните, что нужно приложить или указать в заявке.</small></div>
      <label className="checkbox-field template-choice"><input type="checkbox" checked={titleEditable} onChange={(event) => setTitleEditable(event.target.checked)} /><span><strong>Разрешить менять тему заявки</strong><small>Пользователь сможет уточнить тему перед отправкой.</small></span></label>
      <label className="checkbox-field template-choice"><input type="checkbox" checked={descriptionRequired} onChange={(event) => setDescriptionRequired(event.target.checked)} /><span><strong>Сделать описание заявки обязательным</strong><small>Без описания заявку нельзя будет отправить.</small></span></label>
      <div className="template-control-with-help"><Select label="Исполнитель по умолчанию" value={assigneeId} onChange={(event) => setAssigneeId(event.target.value)}><option value="">Не назначать автоматически</option>{assignees.map((user) => <option key={user.id} value={user.id}>{user.display_name}</option>)}</Select><small className="field-help">При необходимости этот исполнитель получит новую заявку сразу после отправки.</small></div>
    </div>
    <div className="button-row"><Button onClick={() => void save()}><Save size={15} />Сохранить настройки формы</Button></div>
  </Card>;
}

function FieldEditor({ draft, fields, dictionaries, editingId, onChange, onSave, onCancel }: { draft: EditorDraft; fields: FieldReference[]; dictionaries: AdminDictionary[]; editingId: string | null; onChange: (draft: EditorDraft) => void; onSave: () => void; onCancel: () => void }) {
  const update = (patch: Partial<EditorDraft>) => onChange({ ...draft, ...patch });
  const generatedKey = editingId ? draft.key : createSystemSlug(draft.label);
  const isChoice = draft.field_type === "select" || draft.field_type === "multiselect";
  const hasValidation = ["number", "text", "textarea", "rich_text", "email", "file"].includes(draft.field_type);
  const title = editingId ? "Редактирование поля" : "Добавьте поле";

  return <Card className="template-field-editor">
    <div className="template-editor-intro">
      <div><h3>{title}</h3><p>Сначала назовите поле так, как его увидит пользователь. Настройки ниже можно добавлять постепенно.</p></div>
      {editingId ? <Button variant="ghost" onClick={onCancel}>Отменить редактирование</Button> : null}
    </div>

    <section className="template-editor-step" aria-labelledby="field-basics-heading">
      <div className="template-section-title"><span className="template-step-number">1</span><div><h4 id="field-basics-heading">Что спросить у пользователя</h4><p className="muted">Название отображается в форме заявки.</p></div></div>
      <div className="template-step-grid">
        <div className="template-control-with-help"><Input label="Название поля для пользователя" value={draft.label} placeholder="Например, дата занятия" onChange={(event) => update({ label: event.target.value, key: editingId ? draft.key : createSystemSlug(event.target.value) })} /><small className="field-help">Пишите простыми словами: «Номер аудитории», «ФИО преподавателя», «Дата занятия».</small></div>
      </div>
    </section>

    <section className="template-editor-step" aria-labelledby="field-type-heading">
      <div className="template-section-title"><span className="template-step-number">2</span><div><h4 id="field-type-heading">Какой ответ ожидать</h4><p className="muted">Тип определяет, какое поле увидит пользователь и как мы проверим ответ.</p></div></div>
      <div className="template-step-grid">
        <div className="template-control-with-help"><Select label="Тип ответа" value={draft.field_type} disabled={Boolean(editingId)} onChange={(event) => update({ field_type: event.target.value as ServiceDeskTemplateFieldType })}>{fieldTypes.map((type) => <option key={type} value={type}>{fieldTypeLabel(type)}</option>)}</Select><small className="field-help">Выберите «Список» для готовых вариантов, «Файл» для вложений, «Дата и время» для расписания.</small></div>
        <div className="template-control-with-help"><Input label="Пример ответа (необязательно)" value={draft.placeholder} placeholder="Например, 305" onChange={(event) => update({ placeholder: event.target.value })} /><small className="field-help">Серый пример внутри поля; он не отправляется как ответ.</small></div>
        <div className="template-control-with-help template-step-wide"><Input label="Подсказка для пользователя (необязательно)" value={draft.help_text} placeholder="Укажите дату и время по расписанию" onChange={(event) => update({ help_text: event.target.value })} /><small className="field-help">Появится под полем и поможет заполнить его без лишних вопросов.</small></div>
        {isChoice ? <ChoiceSource draft={draft} dictionaries={dictionaries} onChange={update} /> : null}
      </div>
      {hasValidation ? <ValidationSettings draft={draft} onChange={update} /> : null}
    </section>

    <section className="template-editor-step" aria-labelledby="field-rules-heading">
      <div className="template-section-title"><span className="template-step-number">3</span><div><h4 id="field-rules-heading">Когда спрашивать это поле</h4><p className="muted">Правила необязательны. Оставьте их выключенными, если поле нужно всегда.</p></div></div>
      <label className="checkbox-field template-choice template-required-choice"><input type="checkbox" checked={draft.is_required} onChange={(event) => update({ is_required: event.target.checked })} /><span><strong>Это поле обязательно всегда</strong><small>Пользователь не сможет отправить заявку, пока не заполнит это поле.</small></span></label>
      <ConditionSection kind="visibility" rules={draft.visibility_rules} fields={fields} ownKey={draft.key} onChange={(rules) => update({ visibility_rules: rules })} />
      <ConditionSection kind="required" rules={draft.required_rules} fields={fields} ownKey={draft.key} onChange={(rules) => update({ required_rules: rules })} />
    </section>

    <div className="template-editor-footer">
      <div><Button onClick={onSave} disabled={!generatedKey || !draft.label.trim()}><Save size={15} />Сохранить поле</Button>{editingId ? <Button variant="ghost" onClick={onCancel}>Отмена</Button> : null}</div>
      {!generatedKey || !draft.label.trim() ? <small className="field-help">Чтобы сохранить поле, заполните его название.</small> : null}
    </div>
  </Card>;
}

function ChoiceSource({ draft, dictionaries, onChange }: { draft: EditorDraft; dictionaries: AdminDictionary[]; onChange: (patch: Partial<EditorDraft>) => void }) {
  return <>
    <div className="template-control-with-help"><Select label="Откуда брать варианты" value={draft.options_mode} onChange={(event) => onChange({ options_mode: event.target.value as "static" | "dictionary" })}><option value="static">Ввести варианты вручную</option><option value="dictionary">Взять из справочника</option></Select><small className="field-help">Справочник пригодится, если один и тот же список нужен в нескольких формах.</small></div>
    {draft.options_mode === "static" ? <div className="template-control-with-help"><Input label="Варианты списка" value={draft.options_text} placeholder="Очная, заочная" onChange={(event) => onChange({ options_text: event.target.value })} /><small className="field-help">Введите понятные варианты через запятую. Система сама подготовит их для сохранения.</small></div> : <div className="template-control-with-help"><Select label="Справочник" value={draft.dictionary_code} onChange={(event) => onChange({ dictionary_code: event.target.value, options_text: "" })}><option value="">Выберите справочник</option>{dictionaries.map((dictionary) => <option key={dictionary.id} value={dictionary.code}>{dictionary.title}</option>)}</Select><small className="field-help">Пользователь увидит актуальные варианты из выбранного справочника.</small></div>}
  </>;
}

function ValidationSettings({ draft, onChange }: { draft: EditorDraft; onChange: (patch: Partial<EditorDraft>) => void }) {
  return <details className="template-advanced-settings">
    <summary>Дополнительные ограничения</summary>
    <p className="muted">Их можно не заполнять. Используйте ограничения, только если форма должна проверить ответ автоматически.</p>
    <div className="template-step-grid">
      {draft.field_type === "number" ? <><Input label="Минимальное значение" value={draft.min} onChange={(event) => onChange({ min: event.target.value })} /><Input label="Максимальное значение" value={draft.max} onChange={(event) => onChange({ max: event.target.value })} /></> : null}
      {["text", "textarea", "rich_text", "email"].includes(draft.field_type) ? <><Input label="Минимум символов" value={draft.min_length} onChange={(event) => onChange({ min_length: event.target.value })} /><Input label="Максимум символов" value={draft.max_length} onChange={(event) => onChange({ max_length: event.target.value })} /></> : null}
      {draft.field_type === "file" ? <><div className="template-control-with-help"><Input label="Разрешённые расширения" value={draft.allowed_extensions} placeholder="pdf, docx, xlsx" onChange={(event) => onChange({ allowed_extensions: event.target.value })} /><small className="field-help">Перечислите через запятую. Оставьте пустым, чтобы разрешить любые файлы.</small></div><Input label="Максимум файлов" value={draft.max_files} onChange={(event) => onChange({ max_files: event.target.value })} /></> : null}
    </div>
  </details>;
}

function ConditionSection({ kind, rules, fields, ownKey, onChange }: { kind: RuleKind; rules: Rule[]; fields: FieldReference[]; ownKey: string; onChange: (rules: Rule[]) => void }) {
  const isVisibility = kind === "visibility";
  const availableFields = fields.filter((field) => field.key !== ownKey);
  const enabled = rules.length > 0;
  const label = isVisibility ? "Показывать это поле только при выполнении условия" : "Сделать это поле обязательным только при выполнении условия";
  const explanation = isVisibility
    ? "Например, показывать поле «ФИО заменяющего преподавателя», только если пользователь выбрал «Нужен заменяющий преподаватель» — «Да»."
    : "Например, требовать номер приказа только для заявок с выбранной категорией «Перевод».";
  const addRule = () => onChange([...rules, { field: availableFields[0]?.key ?? "", operator: "equals", value: "" }]);
  const updateRule = (index: number, patch: Partial<Rule>) => onChange(rules.map((rule, ruleIndex) => ruleIndex === index ? { ...rule, ...patch } : rule));

  return <section className="template-condition-section" aria-label={isVisibility ? "Условия показа поля" : "Условия обязательности поля"}>
    <label className="checkbox-field template-choice">
      <input type="checkbox" checked={enabled} disabled={!availableFields.length && !enabled} onChange={(event) => event.target.checked ? addRule() : onChange([])} />
      <span><strong>{label}</strong><small>{explanation}</small></span>
    </label>
    {!availableFields.length && !enabled ? <p className="template-condition-hint">Сначала сохраните хотя бы одно другое поле. Тогда можно будет выбрать, от какого ответа зависит это поле.</p> : null}
    {enabled ? <div className="template-condition-editor">
      <p className="template-condition-summary">Если добавите несколько условий, должны выполниться все. Обычно достаточно одного условия.</p>
      {rules.map((rule, index) => {
        const operator = String(rule.operator ?? "equals");
        const isUnknownField = Boolean(rule.field) && !availableFields.some((field) => field.key === rule.field);
        return <div className="template-condition-rule" key={`${kind}-${index}`}>
          <div className="template-condition-rule-heading"><strong>Условие {index + 1}</strong>{rules.length > 1 ? <Button variant="ghost" onClick={() => onChange(rules.filter((_, ruleIndex) => ruleIndex !== index))}><Trash2 size={14} />Удалить условие</Button> : null}</div>
          <div className="template-step-grid template-condition-grid">
            <Select label={`Поле для условия ${isVisibility ? "видимости" : "обязательности"} ${index + 1}`} value={String(rule.field ?? "")} onChange={(event) => updateRule(index, { field: event.target.value })}>
              <option value="">Выберите поле</option>
              {availableFields.map((field) => <option key={field.key} value={field.key}>{field.label}</option>)}
              {isUnknownField ? <option value={String(rule.field)}>Недоступное поле</option> : null}
            </Select>
            <Select label={`Проверка для условия ${index + 1}`} value={operator} onChange={(event) => updateRule(index, { operator: event.target.value })}>{operators.map((item) => <option key={item} value={item}>{operatorLabel(item)}</option>)}</Select>
            {!["is_empty", "is_not_empty"].includes(operator) ? <Input label={`Значение для условия ${index + 1}`} value={ruleValue(rule.value)} onChange={(event) => updateRule(index, { value: event.target.value })} /> : null}
          </div>
          {isUnknownField ? <p className="field-error">Выберите доступное поле: прежнее поле было удалено или это поле нельзя использовать для самого себя.</p> : null}
        </div>;
      })}
      <Button variant="secondary" onClick={addRule}><Plus size={14} />Добавить ещё условие</Button>
    </div> : null}
  </section>;
}

function TemplatePreview({ fields }: { fields: ServiceDeskTemplateField[] }) {
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [users, setUsers] = useState<Array<{ id: string; display_name: string }>>([]);

  useEffect(() => {
    if (fields.some((field) => field.field_type === "user")) getServiceDeskUserOptions().then(setUsers).catch(() => setUsers([]));
  }, [fields]);

  return <Card className="template-preview-card"><h3>Предпросмотр формы</h3><p className="muted">Так форма выглядит для пользователя. Условия отображения зависят от выбранных ответов.</p><div className="service-desk-form-grid"><ServiceDeskDynamicFields fields={fields} values={values} users={users} mode="preview" onChange={(key, value) => setValues((current) => ({ ...current, [key]: value }))} /></div></Card>;
}

function buildPayload(draft: EditorDraft, position: number) {
  const validation: Record<string, unknown> = {};
  if (draft.min) validation.min = Number(draft.min);
  if (draft.max) validation.max = Number(draft.max);
  if (draft.min_length) validation.min_length = Number(draft.min_length);
  if (draft.max_length) validation.max_length = Number(draft.max_length);
  if (draft.allowed_extensions) validation.allowed_extensions = draft.allowed_extensions.split(",").map((item) => item.trim()).filter(Boolean);
  if (draft.max_files) validation.max_files = Number(draft.max_files);
  const visibilityRules = cleanRules(draft.visibility_rules);
  const requiredRules = cleanRules(draft.required_rules);
  const payload: Record<string, unknown> = { key: draft.key.trim(), label: draft.label.trim(), field_type: draft.field_type, is_required: draft.is_required, position, placeholder: draft.placeholder.trim() || null, help_text: draft.help_text.trim() || null, validation: Object.keys(validation).length ? validation : null };
  if (draft.options_mode === "dictionary" && draft.dictionary_code.trim()) {
    payload.dictionary_code = draft.dictionary_code.trim();
    payload.options = null;
  } else {
    payload.dictionary_code = null;
    payload.options = draft.options_text.split(",").map((item) => item.trim()).filter(Boolean).map((label) => ({ label, value: createSystemSlug(label) }));
  }
  payload.visibility_rules = visibilityRules.length ? visibilityRules : null;
  payload.required_rules = requiredRules.length ? requiredRules : null;
  return payload as { key: string; label: string; field_type: ServiceDeskTemplateFieldType; is_required: boolean; position: number };
}

function cleanRules(rules: Rule[]) {
  return rules.filter((rule) => Boolean(rule.field)).map((rule) => ({ field: String(rule.field), operator: String(rule.operator ?? "equals"), value: rule.value ?? "" }));
}

function emptyDraft(): EditorDraft {
  return { key: "", label: "", field_type: "text", is_required: false, placeholder: "", help_text: "", options_mode: "static", options_text: "", dictionary_code: "", min: "", max: "", min_length: "", max_length: "", allowed_extensions: "", max_files: "", visibility_rules: [], required_rules: [] };
}

function fromField(field: ServiceDeskTemplateField): EditorDraft {
  return { ...emptyDraft(), key: field.key, label: field.label, field_type: field.field_type, is_required: field.is_required, placeholder: field.placeholder ?? "", help_text: field.help_text ?? "", options_mode: field.dictionary_code ? "dictionary" : "static", options_text: (field.options ?? []).map((option) => String(option.label ?? option.value ?? "")).join(", "), dictionary_code: field.dictionary_code ?? "", min: String(field.validation?.min ?? ""), max: String(field.validation?.max ?? ""), min_length: String(field.validation?.min_length ?? ""), max_length: String(field.validation?.max_length ?? ""), allowed_extensions: Array.isArray(field.validation?.allowed_extensions) ? field.validation.allowed_extensions.join(", ") : "", max_files: String(field.validation?.max_files ?? ""), visibility_rules: toRules(field.visibility_rules), required_rules: toRules(field.required_rules) };
}

function toRules(value: ServiceDeskTemplateField["visibility_rules"]): Rule[] {
  if (!value) return [];
  return (Array.isArray(value) ? value : [value]).map((rule) => ({ field: typeof rule.field === "string" ? rule.field : "", operator: typeof rule.operator === "string" ? rule.operator : "equals", value: rule.value }));
}

function ruleValue(value: unknown) {
  return Array.isArray(value) ? value.join(", ") : typeof value === "string" || typeof value === "number" ? String(value) : "";
}

function versionStatusLabel(status: AdminTemplateVersion["status"]) {
  return status === "draft" ? "Черновик" : status === "published" ? "Опубликована" : "Архив";
}

function fieldTypeLabel(type: string) {
  const labels: Record<string, string> = { text: "Короткий текст", textarea: "Большой текст", rich_text: "Многострочный текст", select: "Список", multiselect: "Несколько значений", date: "Дата", time: "Время", datetime: "Дата и время", email: "Email", number: "Число", checkbox: "Флажок", file: "Файл", user: "Пользователь" };
  return labels[type] ?? "Поле";
}

function operatorLabel(operator: string) {
  const labels: Record<string, string> = { equals: "равно", not_equals: "не равно", in: "в списке значений", not_in: "не в списке значений", is_empty: "не заполнено", is_not_empty: "заполнено" };
  return labels[operator] ?? operator;
}

function ConfigError({ error }: { error: string | null }) {
  return error ? <p className="form-error" role="alert">{error}</p> : null;
}

function errorText(reason: unknown, fallback: string) {
  return reason instanceof Error ? reason.message : fallback;
}
