import { CalendarCheck, Plus } from "lucide-react";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { FileInput } from "../../../entities/attachment/ui/FileInput";
import { AttachmentList } from "../../../entities/attachment/ui/AttachmentList";
import type { ProjectDetails, ProjectMember } from "../../../entities/project/model/types";
import {
  createAdminProjectStage,
  createAdminProjectTask,
  getAdminProjectStages,
  getMyProjectTasks,
  updateAdminProjectTask,
  updateMyProjectTaskStatus,
  uploadProjectTaskAttachment
} from "../../../entities/project-task/api/projectTaskApi";
import type {
  ProjectStageWithTasks,
  ProjectTask,
  ProjectTaskPayload,
  ProjectTaskStatus
} from "../../../entities/project-task/model/types";
import { formatDate } from "../../../shared/lib/date";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";
import { Textarea } from "../../../shared/ui/Textarea";

const EMPTY_STAGE_ID = "00000000-0000-0000-0000-000000000000";

const statusLabels: Record<ProjectTaskStatus, string> = {
  todo: "Не начата",
  in_progress: "В работе",
  done: "Выполнена",
  cancelled: "Отменена"
};

type MemberOption = Pick<ProjectMember, "id" | "full_name" | "email">;

export function ProjectTasksPanel({
  project,
  mode
}: {
  project: ProjectDetails;
  mode: "manage" | "assigned";
}) {
  const [stages, setStages] = useState<ProjectStageWithTasks[]>([]);
  const [assignedTasks, setAssignedTasks] = useState<ProjectTask[]>([]);
  const [stageForm, setStageForm] = useState({ title: "", start_date: "", end_date: "" });
  const [taskForm, setTaskForm] = useState({
    title: "",
    description: "",
    stage_id: "",
    assignee_user_id: "",
    due_date: ""
  });
  const [filesByTask, setFilesByTask] = useState<Record<string, File[]>>({});
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [busyTaskId, setBusyTaskId] = useState<string | null>(null);

  const assignees = useMemo(() => getAssignees(project), [project]);

  const loadTasks = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      if (mode === "manage") {
        setStages(await getAdminProjectStages(project.id));
      } else {
        setAssignedTasks(await getMyProjectTasks(project.id));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить задачи");
    } finally {
      setIsLoading(false);
    }
  }, [mode, project.id]);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  async function handleCreateStage(event: FormEvent) {
    event.preventDefault();
    if (stageForm.title.trim().length < 2) {
      setError("Название этапа должно быть не короче 2 символов");
      return;
    }
    try {
      setIsSubmitting(true);
      setError(null);
      await createAdminProjectStage(project.id, {
        title: stageForm.title.trim(),
        position: stages.filter((stage) => stage.id !== EMPTY_STAGE_ID).length,
        start_date: stageForm.start_date || null,
        end_date: stageForm.end_date || null
      });
      setStageForm({ title: "", start_date: "", end_date: "" });
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось создать этап");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleCreateTask(event: FormEvent) {
    event.preventDefault();
    if (taskForm.title.trim().length < 2) {
      setError("Название задачи должно быть не короче 2 символов");
      return;
    }
    try {
      setIsSubmitting(true);
      setError(null);
      const payload: ProjectTaskPayload = {
        title: taskForm.title.trim(),
        description: taskForm.description.trim() || null,
        stage_id: taskForm.stage_id || null,
        assignee_user_id: taskForm.assignee_user_id || null,
        status: "todo",
        due_date: taskForm.due_date || null
      };
      await createAdminProjectTask(project.id, payload);
      setTaskForm({ title: "", description: "", stage_id: "", assignee_user_id: "", due_date: "" });
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось создать задачу");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function updateTaskStatus(task: ProjectTask, status: ProjectTaskStatus) {
    try {
      setBusyTaskId(task.id);
      setError(null);
      if (mode === "manage") {
        await updateAdminProjectTask(project.id, task.id, { status });
      } else {
        await updateMyProjectTaskStatus(task.id, status);
      }
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось изменить статус задачи");
    } finally {
      setBusyTaskId(null);
    }
  }

  async function uploadTaskFiles(task: ProjectTask) {
    const files = filesByTask[task.id] ?? [];
    if (files.length === 0) {
      return;
    }
    try {
      setBusyTaskId(task.id);
      setError(null);
      await Promise.all(files.map((file) => uploadProjectTaskAttachment(task.id, file)));
      setFilesByTask((current) => ({ ...current, [task.id]: [] }));
      await loadTasks();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось прикрепить результат");
    } finally {
      setBusyTaskId(null);
    }
  }

  return (
    <Card className="project-tasks-panel">
      <div className="section-heading">
        <h3>Задачи</h3>
      </div>

      {mode === "manage" && (
        <div className="project-task-forms">
          <form className="task-stage-form" onSubmit={handleCreateStage}>
            <Input
              label="Этап"
              name="stage_title"
              value={stageForm.title}
              onChange={(event) => setStageForm({ ...stageForm, title: event.target.value })}
              placeholder="Например: Подготовка"
            />
            <Input
              label="Старт"
              name="stage_start_date"
              type="date"
              value={stageForm.start_date}
              onChange={(event) => setStageForm({ ...stageForm, start_date: event.target.value })}
            />
            <Input
              label="Финиш"
              name="stage_end_date"
              type="date"
              value={stageForm.end_date}
              onChange={(event) => setStageForm({ ...stageForm, end_date: event.target.value })}
            />
            <Button type="submit" disabled={isSubmitting}>
              <Plus size={16} />
              Добавить этап
            </Button>
          </form>

          <form className="task-create-form" onSubmit={handleCreateTask}>
            <Input
              label="Задача"
              name="task_title"
              value={taskForm.title}
              onChange={(event) => setTaskForm({ ...taskForm, title: event.target.value })}
              placeholder="Название задачи"
            />
            <Select
              label="Этап"
              name="task_stage"
              value={taskForm.stage_id}
              onChange={(event) => setTaskForm({ ...taskForm, stage_id: event.target.value })}
            >
              <option value="">Без этапа</option>
              {stages
                .filter((stage) => stage.id !== EMPTY_STAGE_ID)
                .map((stage) => (
                  <option key={stage.id} value={stage.id}>
                    {stage.title}
                  </option>
                ))}
            </Select>
            <Select
              label="Исполнитель"
              name="task_assignee"
              value={taskForm.assignee_user_id}
              onChange={(event) => setTaskForm({ ...taskForm, assignee_user_id: event.target.value })}
            >
              <option value="">Не назначен</option>
              {assignees.map((assignee) => (
                <option key={assignee.id} value={assignee.id}>
                  {assignee.full_name}
                </option>
              ))}
            </Select>
            <Input
              label="Дедлайн"
              name="task_due_date"
              type="date"
              value={taskForm.due_date}
              onChange={(event) => setTaskForm({ ...taskForm, due_date: event.target.value })}
            />
            <Textarea
              label="Описание"
              name="task_description"
              value={taskForm.description}
              onChange={(event) => setTaskForm({ ...taskForm, description: event.target.value })}
              rows={3}
            />
            <Button type="submit" disabled={isSubmitting}>
              <Plus size={16} />
              Добавить задачу
            </Button>
          </form>
        </div>
      )}

      {error && <p className="form-error">{error}</p>}
      {isLoading ? (
        <Spinner />
      ) : mode === "manage" ? (
        <div className="task-stage-list">
          {stages.length === 0 ? (
            <p className="muted">Задач пока нет.</p>
          ) : (
            stages.map((stage) => (
              <section className="task-stage" key={stage.id}>
                <div className="task-stage-heading">
                  <h4>{stage.title}</h4>
                  {(stage.start_date || stage.end_date) && (
                    <span>
                      <CalendarCheck size={14} />
                      {formatStageDates(stage.start_date, stage.end_date)}
                    </span>
                  )}
                </div>
                <TaskList
                  busyTaskId={busyTaskId}
                  filesByTask={filesByTask}
                  mode={mode}
                  onFilesChange={(taskId, files) => setFilesByTask((current) => ({ ...current, [taskId]: files }))}
                  onStatusChange={updateTaskStatus}
                  onUpload={uploadTaskFiles}
                  tasks={stage.tasks}
                />
              </section>
            ))
          )}
        </div>
      ) : assignedTasks.length === 0 ? (
        <p className="muted">Назначенных задач пока нет.</p>
      ) : (
        <TaskList
          busyTaskId={busyTaskId}
          filesByTask={filesByTask}
          mode={mode}
          onFilesChange={(taskId, files) => setFilesByTask((current) => ({ ...current, [taskId]: files }))}
          onStatusChange={updateTaskStatus}
          onUpload={uploadTaskFiles}
          tasks={assignedTasks}
        />
      )}
    </Card>
  );
}

function TaskList({
  busyTaskId,
  filesByTask,
  mode,
  onFilesChange,
  onStatusChange,
  onUpload,
  tasks
}: {
  busyTaskId: string | null;
  filesByTask: Record<string, File[]>;
  mode: "manage" | "assigned";
  onFilesChange: (taskId: string, files: File[]) => void;
  onStatusChange: (task: ProjectTask, status: ProjectTaskStatus) => void;
  onUpload: (task: ProjectTask) => void;
  tasks: ProjectTask[];
}) {
  if (tasks.length === 0) {
    return <p className="muted">Задач нет.</p>;
  }

  return (
    <div className="task-list-grid">
      {tasks.map((task) => (
        <article className={`task-card ${task.is_overdue ? "task-card-overdue" : ""}`} key={task.id}>
          <div className="task-card-heading">
            <strong>{task.title}</strong>
            <span className={`task-status task-status-${task.status}`}>{statusLabels[task.status]}</span>
          </div>
          {task.description && <p>{task.description}</p>}
          <dl className="task-meta">
            <div>
              <dt>Исполнитель</dt>
              <dd>{task.assignee?.full_name ?? "Не назначен"}</dd>
            </div>
            <div>
              <dt>Дедлайн</dt>
              <dd className={task.is_overdue ? "task-overdue-text" : ""}>{formatDate(task.due_date)}</dd>
            </div>
          </dl>
          <Select
            label="Статус"
            name={`task_status_${task.id}`}
            value={task.status}
            disabled={busyTaskId === task.id}
            onChange={(event) => onStatusChange(task, event.target.value as ProjectTaskStatus)}
          >
            <option value="todo">Не начата</option>
            <option value="in_progress">В работе</option>
            <option value="done">Выполнена</option>
            {mode === "manage" && <option value="cancelled">Отменена</option>}
          </Select>
          <AttachmentList attachments={task.attachments} />
          <div className="task-result-upload">
            <FileInput
              files={filesByTask[task.id] ?? []}
              label="Прикрепить результат"
              onChange={(files) => onFilesChange(task.id, files)}
            />
            <Button
              type="button"
              variant="secondary"
              disabled={busyTaskId === task.id || (filesByTask[task.id] ?? []).length === 0}
              onClick={() => onUpload(task)}
            >
              Загрузить
            </Button>
          </div>
        </article>
      ))}
    </div>
  );
}

function getAssignees(project: ProjectDetails): MemberOption[] {
  const users = new Map<string, MemberOption>();
  project.members
    .filter((member) => member.member_role === "working_group_member")
    .forEach((member) => users.set(member.id, member));
  if (project.responsible) {
    users.set(project.responsible.id, project.responsible);
  }
  return Array.from(users.values());
}

function formatStageDates(startDate: string | null, endDate: string | null) {
  if (!startDate && !endDate) {
    return "";
  }
  return `${formatDate(startDate)}${endDate ? ` - ${formatDate(endDate)}` : ""}`;
}
