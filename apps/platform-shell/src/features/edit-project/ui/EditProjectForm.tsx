import { FormEvent, useEffect, useState } from "react";

import type { ProjectDetails, ProjectMutationPayload } from "../../../entities/project/model/types";
import type { User } from "../../../entities/user/model/types";
import { getUserDirectory } from "../../../entities/user/api/userApi";
import { normalizeCompetencyBlocks } from "../../../entities/competency/lib/competencyBlocks";
import {
  normalizeProjectPayload,
  ProjectFormFields,
  validateProjectForm
} from "../../../entities/project/ui/ProjectFormFields";
import { FileInput } from "../../../entities/attachment/ui/FileInput";
import { Button } from "../../../shared/ui/Button";
import { editProjectWithFiles } from "../api/editProject";

function projectToForm(project: ProjectDetails): ProjectMutationPayload {
  return {
    title: project.title,
    short_description: project.short_description,
    description: project.description,
    goal: project.goal,
    expected_result: project.expected_result,
    project_type: project.project_type,
    priority: project.priority,
    status: project.status,
    start_date: project.start_date,
    end_date: project.end_date,
    responsible_user_id: project.responsible?.id ?? null,
    working_group_member_ids: project.members
      .filter((member) => member.member_role === "working_group_member")
      .map((member) => member.id),
    contact_email: project.contact_email,
    required_competencies: project.required_competencies,
    competency_blocks: normalizeCompetencyBlocks(project.competency_blocks, project.required_competencies),
    planned_tasks: project.planned_tasks
  };
}

export function EditProjectForm({
  project,
  onSaved
}: {
  project: ProjectDetails;
  onSaved: (project: ProjectDetails) => void;
}) {
  const [form, setForm] = useState<ProjectMutationPayload>(projectToForm(project));
  const [files, setFiles] = useState<File[]>([]);
  const [responsibleUsers, setResponsibleUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isUsersLoading, setIsUsersLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let ignore = false;
    async function loadUsers() {
      try {
        setIsUsersLoading(true);
        const users = await getUserDirectory();
        if (!ignore) {
          setResponsibleUsers(users);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Не удалось загрузить список ответственных");
        }
      } finally {
        if (!ignore) {
          setIsUsersLoading(false);
        }
      }
    }
    void loadUsers();
    return () => {
      ignore = true;
    };
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const validationError = validateProjectForm(form);
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      const updatedProject = await editProjectWithFiles(project.id, normalizeProjectPayload(form), files);
      setFiles([]);
      onSaved(updatedProject);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить проект");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-panel" onSubmit={handleSubmit}>
      <ProjectFormFields
        form={form}
        setForm={setForm}
        responsibleUsers={responsibleUsers}
        isResponsibleUsersLoading={isUsersLoading}
      />
      <FileInput files={files} label="Добавить файлы к проекту" onChange={setFiles} />
      {error && <p className="form-error">{error}</p>}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Сохраняем" : "Сохранить"}
      </Button>
    </form>
  );
}
