import type { ProjectMutationPayload } from "../model/types";
import type { User } from "@prom/auth";
import { CompetencyBlocksEditor } from "../../competency/ui/CompetencyBlocksEditor";
import {
  createEmptyCompetencyBlock,
  flattenCompetencyBlocks,
  normalizeCompetencyBlocks,
} from "../../competency/lib/competencyBlocks";
import { Input } from "@prom/ui/Input";
import { Select } from "@prom/ui/Select";
import { Textarea } from "@prom/ui/Textarea";
import { isUtmnEmail, normalizeEmail } from "@prom/utils/email";

export const emptyProjectForm: ProjectMutationPayload = {
  title: "",
  short_description: "",
  description: "",
  goal: "",
  expected_result: "",
  project_type: "strategic",
  priority: "high",
  status: "active",
  start_date: null,
  end_date: null,
  responsible_user_id: null,
  working_group_member_ids: [],
  contact_email: "project.manager@utmn.ru",
  required_competencies: "",
  competency_blocks: [createEmptyCompetencyBlock()],
  planned_tasks: "",
};

const REQUIRED_TEXT_FIELDS: Array<{
  field: keyof ProjectMutationPayload;
  label: string;
}> = [
  { field: "title", label: "Название" },
  { field: "short_description", label: "Краткое описание" },
  { field: "description", label: "Полное описание" },
  { field: "goal", label: "Цель" },
];

function normalizeRequiredText(
  value: ProjectMutationPayload[keyof ProjectMutationPayload],
) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeOptionalText(value: string | null | undefined) {
  return value?.trim() || null;
}

export function normalizeProjectPayload(
  form: ProjectMutationPayload,
): ProjectMutationPayload {
  const competencyBlocks = normalizeCompetencyBlocks(
    form.competency_blocks,
    form.required_competencies,
  );
  const requiredCompetencies = flattenCompetencyBlocks(competencyBlocks);

  return {
    ...form,
    title: form.title.trim(),
    short_description: form.short_description.trim(),
    description: form.description.trim(),
    goal: form.goal.trim(),
    expected_result: normalizeOptionalText(form.expected_result),
    start_date: form.start_date || null,
    end_date: form.end_date || null,
    responsible_user_id: form.responsible_user_id || null,
    working_group_member_ids: form.working_group_member_ids ?? [],
    contact_email: normalizeOptionalText(
      form.contact_email ? normalizeEmail(form.contact_email) : null,
    ),
    required_competencies: normalizeOptionalText(
      requiredCompetencies || form.required_competencies,
    ),
    competency_blocks: competencyBlocks,
    planned_tasks: normalizeOptionalText(form.planned_tasks),
  };
}

export function validateProjectForm(form: ProjectMutationPayload) {
  for (const field of REQUIRED_TEXT_FIELDS) {
    if (normalizeRequiredText(form[field.field]).length < 3) {
      return `${field.label}: заполните поле минимум 3 символами`;
    }
  }

  const contactEmail = normalizeOptionalText(form.contact_email);
  if (contactEmail && !isUtmnEmail(contactEmail)) {
    return "Контактный email: введите корректный адрес на домене @utmn.ru";
  }

  const invalidBlock = (form.competency_blocks ?? []).find(
    (block) => block.competencies.length > 0 && block.title.trim().length < 2,
  );
  if (invalidBlock) {
    return "Направление работы: укажите название минимум из 2 символов";
  }

  return null;
}

const ROLE_LABELS: Record<User["role"], string> = {
  platform_admin: "Администратор платформы",
  project_manager: "Руководитель",
  employee: "Сотрудник",
};

export function ProjectFormFields({
  form,
  setForm,
  responsibleUsers = [],
  isResponsibleUsersLoading = false,
}: {
  form: ProjectMutationPayload;
  setForm: (form: ProjectMutationPayload) => void;
  responsibleUsers?: User[];
  isResponsibleUsersLoading?: boolean;
}) {
  const selectedMemberIds = new Set(form.working_group_member_ids ?? []);

  function toggleWorkingGroupMember(userId: string) {
    const nextMemberIds = selectedMemberIds.has(userId)
      ? (form.working_group_member_ids ?? []).filter((id) => id !== userId)
      : [...(form.working_group_member_ids ?? []), userId];
    setForm({ ...form, working_group_member_ids: nextMemberIds });
  }

  return (
    <>
      <div className="form-grid">
        <Input
          label="Название"
          name="title"
          value={form.title}
          onChange={(event) => setForm({ ...form, title: event.target.value })}
          required
        />
        <Input
          label="Краткое описание"
          name="short_description"
          value={form.short_description}
          onChange={(event) =>
            setForm({ ...form, short_description: event.target.value })
          }
          required
        />
      </div>
      <Textarea
        label="Полное описание"
        name="description"
        rows={4}
        value={form.description}
        onChange={(event) =>
          setForm({ ...form, description: event.target.value })
        }
        required
      />
      <Textarea
        label="Цель"
        name="goal"
        rows={3}
        value={form.goal}
        onChange={(event) => setForm({ ...form, goal: event.target.value })}
        required
      />
      <Textarea
        label="Ожидаемый результат"
        name="expected_result"
        rows={3}
        value={form.expected_result ?? ""}
        onChange={(event) =>
          setForm({ ...form, expected_result: event.target.value })
        }
      />
      <div className="form-grid four">
        <Select
          label="Тип"
          name="project_type"
          value={form.project_type}
          onChange={(event) =>
            setForm({
              ...form,
              project_type: event.target
                .value as ProjectMutationPayload["project_type"],
            })
          }
        >
          <option value="strategic">Стратегический</option>
        </Select>
        <Select
          label="Приоритет"
          name="priority"
          value={form.priority}
          onChange={(event) =>
            setForm({
              ...form,
              priority: event.target
                .value as ProjectMutationPayload["priority"],
            })
          }
        >
          <option value="low">Низкий</option>
          <option value="medium">Средний</option>
          <option value="high">Высокий</option>
          <option value="critical">Критичный</option>
        </Select>
        <Select
          label="Статус"
          name="status"
          value={form.status}
          onChange={(event) =>
            setForm({
              ...form,
              status: event.target.value as ProjectMutationPayload["status"],
            })
          }
        >
          <option value="draft">Черновик</option>
          <option value="active">Активен</option>
          <option value="paused">Пауза</option>
          <option value="completed">Завершён</option>
          <option value="archived">Архив</option>
        </Select>
        <Select
          label="Ответственный"
          name="responsible_user_id"
          value={form.responsible_user_id ?? ""}
          onChange={(event) =>
            setForm({
              ...form,
              responsible_user_id: event.target.value || null,
            })
          }
          disabled={isResponsibleUsersLoading}
        >
          <option value="">
            {isResponsibleUsersLoading ? "Загрузка..." : "Не указан"}
          </option>
          {responsibleUsers.map((user) => (
            <option key={user.id} value={user.id}>
              {user.full_name} - {ROLE_LABELS[user.role]}
            </option>
          ))}
        </Select>
      </div>
      <div className="form-grid">
        <Input
          label="Контактный email"
          name="contact_email"
          type="email"
          value={form.contact_email ?? ""}
          onChange={(event) =>
            setForm({ ...form, contact_email: event.target.value })
          }
        />
        <Input
          label="Дата начала"
          name="start_date"
          type="date"
          value={form.start_date ?? ""}
          onChange={(event) =>
            setForm({ ...form, start_date: event.target.value })
          }
        />
        <Input
          label="Дата окончания"
          name="end_date"
          type="date"
          value={form.end_date ?? ""}
          onChange={(event) =>
            setForm({ ...form, end_date: event.target.value })
          }
        />
      </div>
      <CompetencyBlocksEditor
        label="Направления работы и компетенции"
        value={form.competency_blocks ?? [createEmptyCompetencyBlock()]}
        onChange={(competency_blocks) =>
          setForm({ ...form, competency_blocks })
        }
      />
      <div className="member-picker">
        <span className="field-label">Рабочая группа</span>
        {isResponsibleUsersLoading ? (
          <span className="muted">Загружаем пользователей...</span>
        ) : responsibleUsers.length === 0 ? (
          <span className="muted">Пользователи не найдены.</span>
        ) : (
          <div className="member-picker-grid">
            {responsibleUsers.map((user) => (
              <label
                className={
                  selectedMemberIds.has(user.id)
                    ? "member-option member-option-active"
                    : "member-option"
                }
                key={user.id}
              >
                <input
                  type="checkbox"
                  checked={selectedMemberIds.has(user.id)}
                  onChange={() => toggleWorkingGroupMember(user.id)}
                />
                <span>
                  <strong>{user.full_name}</strong>
                  <small>
                    {user.email} - {ROLE_LABELS[user.role]}
                  </small>
                </span>
              </label>
            ))}
          </div>
        )}
      </div>
      <Textarea
        label="Планируемые задачи"
        name="planned_tasks"
        rows={3}
        value={form.planned_tasks ?? ""}
        onChange={(event) =>
          setForm({ ...form, planned_tasks: event.target.value })
        }
      />
    </>
  );
}
