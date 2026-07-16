import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { ArrowDown, ArrowUp, Plus, RefreshCw, Save, Trash2 } from "lucide-react";

import {
  createServiceDeskRoutingRule,
  deleteServiceDeskRoutingRule,
  getServiceDeskRoutingCatalogOptions,
  getServiceDeskRoutingCandidates,
  getServiceDeskRoutingRules,
  reorderServiceDeskRoutingRules,
  updateServiceDeskRoutingRule
} from "../../../entities/service-desk-routing/api/serviceDeskRoutingApi";
import type {
  ServiceDeskRoutingAction,
  ServiceDeskRoutingAssignee,
  ServiceDeskRoutingCondition,
  ServiceDeskRoutingConditionField,
  ServiceDeskRoutingRule,
  ServiceDeskRoutingRulePayload
} from "../../../entities/service-desk-routing/model/types";
import type { ServiceDeskCategory, ServiceDeskService } from "../../../entities/service-desk-catalog/model/types";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { SearchableSelect, type SearchableSelectOption } from "../../../shared/ui/SearchableSelect";
import { Spinner } from "../../../shared/ui/Spinner";

type RoutingActionDraft = {
  type: ServiceDeskRoutingAction["type"];
  userId: string;
  priority: "low" | "medium" | "high" | "critical";
};

type RoutingRuleDraft = {
  name: string;
  priority: string;
  isActive: boolean;
  conditions: ServiceDeskRoutingCondition[];
  action: RoutingActionDraft;
};

const CONDITION_OPTIONS: Array<{ value: ServiceDeskRoutingConditionField; label: string }> = [
  { value: "service_id", label: "Услуга" },
  { value: "category_id", label: "Категория" },
  { value: "priority", label: "Приоритет заявки" },
  { value: "field_value", label: "Значение поля формы" }
];

const PRIORITY_OPTIONS: Array<{ value: RoutingActionDraft["priority"]; label: string }> = [
  { value: "low", label: "Низкий" },
  { value: "medium", label: "Средний" },
  { value: "high", label: "Высокий" },
  { value: "critical", label: "Критический" }
];

function createEmptyDraft(): RoutingRuleDraft {
  return {
    name: "",
    priority: "100",
    isActive: true,
    conditions: [],
    action: { type: "assign_user", userId: "", priority: "medium" }
  };
}

function createEmptyCondition(): ServiceDeskRoutingCondition {
  return { field: "service_id", operator: "equals", value: "" };
}

function toDraft(rule: ServiceDeskRoutingRule): RoutingRuleDraft {
  return {
    name: rule.name,
    priority: String(rule.priority),
    isActive: rule.is_active,
    conditions: rule.conditions.map((condition) => ({ ...condition })),
    action:
      rule.action.type === "assign_user"
        ? { type: "assign_user", userId: rule.action.user_id, priority: "medium" }
        : { type: "set_priority", userId: "", priority: rule.action.priority }
  };
}

function toAction(draft: RoutingActionDraft): ServiceDeskRoutingAction {
  return draft.type === "assign_user"
    ? { type: "assign_user", user_id: draft.userId }
    : { type: "set_priority", priority: draft.priority };
}

function sortOptions(options: SearchableSelectOption[]) {
  return options.toSorted((left, right) => left.label.localeCompare(right.label, "ru"));
}

export function buildRoutingCategoryOptions(categories: ServiceDeskCategory[]) {
  return sortOptions(categories.map((category) => ({ value: category.id, label: category.title })));
}

export function buildRoutingServiceOptions(
  services: ServiceDeskService[],
  categories: ServiceDeskCategory[],
) {
  const categoriesById = new Map(categories.map((category) => [category.id, category.title]));
  return sortOptions(
    services.map((service) => ({
      value: service.id,
      label: `${service.title} · ${service.category?.title ?? categoriesById.get(service.category_id) ?? "Без категории"}`
    }))
  );
}

function conditionLabel(
  condition: ServiceDeskRoutingCondition,
  categoryOptions: SearchableSelectOption[],
  serviceOptions: SearchableSelectOption[],
): string {
  const fieldLabel = CONDITION_OPTIONS.find((item) => item.value === condition.field)?.label ?? condition.field;
  const fieldKey = condition.field === "field_value" ? ` · ${condition.field_key ?? "поле не задано"}` : "";
  const entityOptions = condition.field === "service_id" ? serviceOptions : condition.field === "category_id" ? categoryOptions : [];
  const value = entityOptions.find((option) => option.value === condition.value)?.label ?? condition.value;
  return `${fieldLabel}${fieldKey}: ${value || "любое значение"}`;
}

function actionLabel(action: ServiceDeskRoutingAction, assignees: ServiceDeskRoutingAssignee[]): string {
  if (action.type === "set_priority") {
    return `Установить приоритет: ${PRIORITY_OPTIONS.find((item) => item.value === action.priority)?.label}`;
  }
  const assignee = assignees.find((item) => item.id === action.user_id);
  return `Назначить: ${assignee ? `${assignee.display_name} (${assignee.email})` : action.user_id}`;
}

function RoutingRuleForm({
  assignees,
  categoryOptions,
  draft,
  isSaving,
  serviceOptions,
  onCancel,
  onChange,
  onSubmit
}: {
  assignees: ServiceDeskRoutingAssignee[];
  categoryOptions: SearchableSelectOption[];
  draft: RoutingRuleDraft;
  isSaving: boolean;
  serviceOptions: SearchableSelectOption[];
  onCancel: () => void;
  onChange: (updater: (current: RoutingRuleDraft) => RoutingRuleDraft) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <Card className="service-desk-routing-form-card">
      <div className="service-desk-routing-card-heading">
        <div>
          <span className="service-desk-eyebrow">Правило</span>
          <h2>{draft.name ? "Редактирование правила" : "Новое правило"}</h2>
        </div>
      </div>
      <form className="service-desk-routing-form" onSubmit={onSubmit}>
        <Input
          label="Название"
          value={draft.name}
          onChange={(event) => onChange((current) => ({ ...current, name: event.target.value }))}
          required
        />
        <div className="service-desk-routing-order">
          <Input
            label="Позиция в цепочке"
            type="number"
            min="0"
            value={draft.priority}
            onChange={(event) => onChange((current) => ({ ...current, priority: event.target.value }))}
            required
          />
          <p>Правила проверяются по возрастанию номера: 1 — первым. После сохранения цепочку можно менять стрелками в списке.</p>
        </div>
        <label className="service-desk-routing-check">
          <input
            type="checkbox"
            checked={draft.isActive}
            onChange={(event) => onChange((current) => ({ ...current, isActive: event.target.checked }))}
          />
          <span>Правило активно</span>
        </label>

        <div className="service-desk-routing-form-section">
          <div className="service-desk-routing-card-heading">
            <div>
              <h3>Условия</h3>
              <p>Все условия должны совпасть. Пустой набор применяет правило ко всем заявкам.</p>
            </div>
            <Button
              type="button"
              variant="secondary"
              onClick={() =>
                onChange((current) => ({ ...current, conditions: [...current.conditions, createEmptyCondition()] }))
              }
            >
              <Plus size={16} /> Добавить
            </Button>
          </div>

          {draft.conditions.length === 0 ? (
            <p className="muted">Условия не заданы.</p>
          ) : (
            <div className="service-desk-routing-condition-list">
              {draft.conditions.map((condition, index) => (
                <div
                  className={`service-desk-routing-condition${
                    condition.field === "field_value" ? " service-desk-routing-condition-with-key" : ""
                  }`}
                  key={`${condition.field}-${index}`}
                >
                  <Select
                    aria-label={`Поле условия ${index + 1}`}
                    value={condition.field}
                    onChange={(event) => {
                      const field = event.target.value as ServiceDeskRoutingConditionField;
                      onChange((current) => ({
                        ...current,
                        conditions: current.conditions.map((item, itemIndex) =>
                          itemIndex === index
                            ? { field, operator: "equals", value: "", field_key: undefined }
                            : item
                        )
                      }));
                    }}
                  >
                    {CONDITION_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </Select>
                  {condition.field === "field_value" ? (
                    <Input
                      aria-label={`Ключ поля ${index + 1}`}
                      placeholder="Ключ поля"
                      value={condition.field_key ?? ""}
                      onChange={(event) =>
                        onChange((current) => ({
                          ...current,
                          conditions: current.conditions.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, field_key: event.target.value } : item
                          )
                        }))
                      }
                      required
                    />
                  ) : null}
                  {condition.field === "service_id" || condition.field === "category_id" ? (
                    <SearchableSelect
                      ariaLabel={`Значение условия ${index + 1}: ${condition.field === "service_id" ? "услуга" : "категория"}`}
                      name={`routing-condition-${index}-${condition.field}`}
                      value={condition.value}
                      options={condition.field === "service_id" ? serviceOptions : categoryOptions}
                      placeholder={condition.field === "service_id" ? "Услуга не выбрана" : "Категория не выбрана"}
                      searchPlaceholder={condition.field === "service_id" ? "Найдите или выберите услугу" : "Найдите или выберите категорию"}
                      emptyText={condition.field === "service_id" ? "Услуги не найдены" : "Категории не найдены"}
                      clearLabel={condition.field === "service_id" ? "Очистить выбранную услугу" : "Очистить выбранную категорию"}
                      onChange={(value) =>
                        onChange((current) => ({
                          ...current,
                          conditions: current.conditions.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, value } : item
                          )
                        }))
                      }
                    />
                  ) : condition.field === "priority" ? (
                    <Select
                      aria-label={`Значение условия ${index + 1}`}
                      value={condition.value}
                      onChange={(event) =>
                        onChange((current) => ({
                          ...current,
                          conditions: current.conditions.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, value: event.target.value } : item
                          )
                        }))
                      }
                      required
                    >
                      <option value="">Выберите приоритет</option>
                      {PRIORITY_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </Select>
                  ) : (
                    <Input
                      aria-label={`Значение условия ${index + 1}`}
                      placeholder="Значение"
                      value={condition.value}
                      onChange={(event) =>
                        onChange((current) => ({
                          ...current,
                          conditions: current.conditions.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, value: event.target.value } : item
                          )
                        }))
                      }
                      required
                    />
                  )}
                  <Button
                    type="button"
                    variant="ghost"
                    aria-label={`Удалить условие ${index + 1}`}
                    onClick={() =>
                      onChange((current) => ({
                        ...current,
                        conditions: current.conditions.filter((_, itemIndex) => itemIndex !== index)
                      }))
                    }
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="service-desk-routing-form-section">
          <h3>Действие</h3>
          <Select
            label="Тип действия"
            value={draft.action.type}
            onChange={(event) =>
              onChange((current) => ({
                ...current,
                action: {
                  ...current.action,
                  type: event.target.value as RoutingActionDraft["type"]
                }
              }))
            }
          >
            <option value="assign_user">Назначить исполнителя</option>
            <option value="set_priority">Установить приоритет</option>
          </Select>
          {draft.action.type === "assign_user" ? (
            <Select
              label="Исполнитель"
              value={draft.action.userId}
              onChange={(event) =>
                onChange((current) => ({
                  ...current,
                  action: { ...current.action, userId: event.target.value }
                }))
              }
              required
            >
              <option value="">Выберите исполнителя</option>
              {assignees.map((assignee) => (
                <option key={assignee.id} value={assignee.id}>
                  {assignee.display_name} — {assignee.email}
                </option>
              ))}
            </Select>
          ) : (
            <Select
              label="Новый приоритет"
              value={draft.action.priority}
              onChange={(event) =>
                onChange((current) => ({
                  ...current,
                  action: {
                    ...current.action,
                    priority: event.target.value as RoutingActionDraft["priority"]
                  }
                }))
              }
            >
              {PRIORITY_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          )}
        </div>

        <div className="form-actions">
          <Button type="submit" disabled={isSaving}>
            <Save size={16} /> {isSaving ? "Сохраняем…" : "Сохранить правило"}
          </Button>
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isSaving}>
            Отменить
          </Button>
        </div>
      </form>
    </Card>
  );
}

export function ServiceDeskAdminRoutingPage() {
  const [rules, setRules] = useState<ServiceDeskRoutingRule[]>([]);
  const [assignees, setAssignees] = useState<ServiceDeskRoutingAssignee[]>([]);
  const [categories, setCategories] = useState<ServiceDeskCategory[]>([]);
  const [services, setServices] = useState<ServiceDeskService[]>([]);
  const [draft, setDraft] = useState<RoutingRuleDraft>(createEmptyDraft);
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const loadData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [nextRules, nextAssignees, catalogOptions] = await Promise.all([
        getServiceDeskRoutingRules(),
        getServiceDeskRoutingCandidates(),
        getServiceDeskRoutingCatalogOptions()
      ]);
      setRules(nextRules);
      setAssignees(nextAssignees);
      setCategories(catalogOptions.categories);
      setServices(catalogOptions.services);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить правила маршрутизации");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const resetForm = useCallback(() => {
    setEditingRuleId(null);
    setDraft(createEmptyDraft());
  }, []);

  const categoryOptions = useMemo(() => buildRoutingCategoryOptions(categories), [categories]);
  const serviceOptions = useMemo(() => buildRoutingServiceOptions(services, categories), [services, categories]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (draft.conditions.some((condition) => !condition.value.trim())) {
      setError("Выберите значение для каждого условия маршрутизации.");
      return;
    }
    const payload: ServiceDeskRoutingRulePayload = {
      name: draft.name.trim(),
      priority: Number(draft.priority),
      is_active: draft.isActive,
      conditions: draft.conditions.map((condition) => ({
        ...condition,
        field_key: condition.field === "field_value" ? condition.field_key?.trim() || null : null
      })),
      action: toAction(draft.action)
    };

    try {
      setIsSaving(true);
      setError(null);
      if (editingRuleId) {
        await updateServiceDeskRoutingRule(editingRuleId, payload);
      } else {
        await createServiceDeskRoutingRule(payload);
      }
      resetForm();
      await loadData();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось сохранить правило");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (rule: ServiceDeskRoutingRule) => {
    if (!window.confirm(`Удалить правило «${rule.name}»?`)) {
      return;
    }
    try {
      setError(null);
      await deleteServiceDeskRoutingRule(rule.id);
      if (editingRuleId === rule.id) {
        resetForm();
      }
      await loadData();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось удалить правило");
    }
  };

  const handleMove = async (ruleId: string, direction: -1 | 1) => {
    const currentIndex = rules.findIndex((rule) => rule.id === ruleId);
    const nextIndex = currentIndex + direction;
    if (currentIndex < 0 || nextIndex < 0 || nextIndex >= rules.length) {
      return;
    }
    const nextRuleIds = rules.map((rule) => rule.id);
    [nextRuleIds[currentIndex], nextRuleIds[nextIndex]] = [nextRuleIds[nextIndex], nextRuleIds[currentIndex]];
    try {
      setError(null);
      setRules(await reorderServiceDeskRoutingRules(nextRuleIds));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Не удалось изменить порядок правил");
    }
  };

  return (
    <>
      <PageLayout
        title="Маршрутизация Service Desk"
        subtitle="Правила образуют цепочку и проверяются сверху вниз. Первое подходящее правило назначает исполнителя."
        actions={
          <div className="service-desk-routing-page-actions">
            <Button variant="secondary" onClick={() => void loadData()} disabled={isLoading}>
              <RefreshCw size={16} /> Обновить
            </Button>
            <Button onClick={resetForm}>
              <Plus size={16} /> Новое правило
            </Button>
          </div>
        }
      >
        {error ? <p className="form-error">{error}</p> : null}
        {isLoading ? <Spinner label="Загружаем правила маршрутизации" /> : null}
        {!isLoading ? (
          <div className="service-desk-routing-layout">
            <RoutingRuleForm
              assignees={assignees}
              categoryOptions={categoryOptions}
              draft={draft}
              isSaving={isSaving}
              serviceOptions={serviceOptions}
              onCancel={resetForm}
              onChange={(updater) => setDraft(updater)}
              onSubmit={handleSubmit}
            />
            <section className="service-desk-routing-list">
              {rules.length === 0 ? (
                <Card>
                  <EmptyState
                    title="Правил пока нет"
                    text="Создайте первое правило: оно может назначить исполнителя или изменить приоритет заявки."
                  />
                </Card>
              ) : (
                rules.map((rule, index) => (
                  <Card className="service-desk-routing-rule-card" key={rule.id}>
                    <div className="service-desk-routing-card-heading">
                      <div>
                        <div className="card-topline">
                          <span className="service-desk-routing-priority">Шаг {index + 1} в цепочке</span>
                          <span className={rule.is_active ? "status-badge status-active" : "status-badge status-archived"}>
                            {rule.is_active ? "Активно" : "Выключено"}
                          </span>
                        </div>
                        <h2>{rule.name}</h2>
                      </div>
                      <div className="service-desk-routing-rule-actions">
                        <Button
                          variant="ghost"
                          aria-label={`Переместить правило ${rule.name} выше`}
                          disabled={index === 0}
                          onClick={() => void handleMove(rule.id, -1)}
                        >
                          <ArrowUp size={16} />
                        </Button>
                        <Button
                          variant="ghost"
                          aria-label={`Переместить правило ${rule.name} ниже`}
                          disabled={index === rules.length - 1}
                          onClick={() => void handleMove(rule.id, 1)}
                        >
                          <ArrowDown size={16} />
                        </Button>
                      </div>
                    </div>
                    <div className="service-desk-routing-rule-summary">
                      <div>
                        <span>Условия</span>
                        {rule.conditions.length === 0 ? (
                          <p>Для всех заявок</p>
                        ) : (
                          <ul>
                            {rule.conditions.map((condition, conditionIndex) => (
                              <li key={`${rule.id}-${conditionIndex}`}>{conditionLabel(condition, categoryOptions, serviceOptions)}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                      <div>
                        <span>Действие</span>
                        <p>{actionLabel(rule.action, assignees)}</p>
                      </div>
                    </div>
                    <div className="form-actions">
                      <Button
                        variant="secondary"
                        onClick={() => {
                          setEditingRuleId(rule.id);
                          setDraft(toDraft(rule));
                        }}
                      >
                        Редактировать
                      </Button>
                      <Button variant="danger" onClick={() => void handleDelete(rule)}>
                        <Trash2 size={16} /> Удалить
                      </Button>
                    </div>
                  </Card>
                ))
              )}
            </section>
          </div>
        ) : null}
      </PageLayout>
    </>
  );
}
