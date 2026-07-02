import { FormEvent, useState } from "react";

import type { ProjectDetails, ProjectMutationPayload } from "../../../entities/project/model/types";
import {
  emptyProjectForm,
  normalizeProjectPayload,
  ProjectFormFields
} from "../../../entities/project/ui/ProjectFormFields";
import { FileInput } from "../../../entities/attachment/ui/FileInput";
import { Button } from "../../../shared/ui/Button";
import { createProjectWithFiles } from "../api/createProject";

export function CreateProjectForm({ onCreated }: { onCreated: (project: ProjectDetails) => void }) {
  const [form, setForm] = useState<ProjectMutationPayload>(emptyProjectForm);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
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
      <ProjectFormFields form={form} setForm={setForm} />
      <FileInput files={files} label="Прикрепить файлы к проекту" onChange={setFiles} />
      {error && <p className="form-error">{error}</p>}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Создаём" : "Создать проект"}
      </Button>
    </form>
  );
}
