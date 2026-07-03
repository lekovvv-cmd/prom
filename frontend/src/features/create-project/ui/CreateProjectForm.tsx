import { FormEvent, useEffect, useState } from "react";

import type { ProjectDetails, ProjectMutationPayload } from "../../../entities/project/model/types";
import type { User } from "../../../entities/user/model/types";
import { getAdminUsers } from "../../../entities/user/api/userApi";
import {
  emptyProjectForm,
  normalizeProjectPayload,
  ProjectFormFields,
  validateProjectForm
} from "../../../entities/project/ui/ProjectFormFields";
import { FileInput } from "../../../entities/attachment/ui/FileInput";
import { Button } from "../../../shared/ui/Button";
import { createProjectWithFiles } from "../api/createProject";

export function CreateProjectForm({ onCreated }: { onCreated: (project: ProjectDetails) => void }) {
  const [form, setForm] = useState<ProjectMutationPayload>(emptyProjectForm);
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
        const users = await getAdminUsers();
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
      const project = await createProjectWithFiles(normalizeProjectPayload(form), files);
      setForm(emptyProjectForm);
      setFiles([]);
      onCreated(project);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось создать проект");
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
      <FileInput files={files} label="Прикрепить файлы к проекту" onChange={setFiles} />
      {error && <p className="form-error">{error}</p>}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Создаём" : "Создать проект"}
      </Button>
    </form>
  );
}
