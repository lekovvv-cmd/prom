import type { ProjectMutationPayload } from "../model/types";
import { CompetencyPicker } from "../../competency/ui/CompetencyPicker";
import { Input } from "../../../shared/ui/Input";
import { Select } from "../../../shared/ui/Select";
import { Textarea } from "../../../shared/ui/Textarea";

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
  contact_email: "manager@utmn.ru",
  required_competencies: "",
  planned_tasks: ""
};

export function normalizeProjectPayload(form: ProjectMutationPayload): ProjectMutationPayload {
  return {
    ...form,
    expected_result: form.expected_result || null,
    start_date: form.start_date || null,
    end_date: form.end_date || null,
    responsible_user_id: form.responsible_user_id || null,
    contact_email: form.contact_email || null,
    required_competencies: form.required_competencies || null,
    planned_tasks: form.planned_tasks || null
  };
}

export function ProjectFormFields({
  form,
  setForm
}: {
  form: ProjectMutationPayload;
  setForm: (form: ProjectMutationPayload) => void;
}) {
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
          onChange={(event) => setForm({ ...form, short_description: event.target.value })}
          required
        />
      </div>
      <Textarea
        label="Полное описание"
        name="description"
        rows={4}
        value={form.description}
        onChange={(event) => setForm({ ...form, description: event.target.value })}
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
        onChange={(event) => setForm({ ...form, expected_result: event.target.value })}
      />
      <div className="form-grid four">
        <Select
          label="Тип"
          name="project_type"
          value={form.project_type}
          onChange={(event) => setForm({ ...form, project_type: event.target.value as ProjectMutationPayload["project_type"] })}
        >
          <option value="strategic">Стратегический</option>
        </Select>
        <Select
          label="Приоритет"
          name="priority"
          value={form.priority}
          onChange={(event) => setForm({ ...form, priority: event.target.value as ProjectMutationPayload["priority"] })}
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
          onChange={(event) => setForm({ ...form, status: event.target.value as ProjectMutationPayload["status"] })}
        >
          <option value="draft">Черновик</option>
          <option value="active">Активен</option>
          <option value="paused">Пауза</option>
          <option value="completed">Завершён</option>
          <option value="archived">Архив</option>
        </Select>
        <Input
          label="Контактный email"
          name="contact_email"
          type="email"
          value={form.contact_email ?? ""}
          onChange={(event) => setForm({ ...form, contact_email: event.target.value })}
        />
      </div>
      <div className="form-grid">
        <Input
          label="Дата начала"
          name="start_date"
          type="date"
          value={form.start_date ?? ""}
          onChange={(event) => setForm({ ...form, start_date: event.target.value })}
        />
        <Input
          label="Дата окончания"
          name="end_date"
          type="date"
          value={form.end_date ?? ""}
          onChange={(event) => setForm({ ...form, end_date: event.target.value })}
        />
      </div>
      <CompetencyPicker
        label="Требуемые компетенции"
        value={form.required_competencies}
        onChange={(required_competencies) => setForm({ ...form, required_competencies })}
      />
      <Textarea
        label="Планируемые задачи"
        name="planned_tasks"
        rows={3}
        value={form.planned_tasks ?? ""}
        onChange={(event) => setForm({ ...form, planned_tasks: event.target.value })}
      />
    </>
  );
}
