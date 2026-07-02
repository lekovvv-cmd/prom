import { FormEvent, useState } from "react";

import type { ProjectDetails, ProjectMutationPayload } from "../../../entities/project/model/types";
import {
  emptyProjectForm,
  normalizeProjectPayload,
  ProjectFormFields
} from "../../../entities/project/ui/ProjectFormFields";
import { Button } from "../../../shared/ui/Button";
import { createProject } from "../api/createProject";

export function CreateProjectForm({ onCreated }: { onCreated: (project: ProjectDetails) => void }) {
  const [form, setForm] = useState<ProjectMutationPayload>(emptyProjectForm);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      setIsSubmitting(true);
      setError(null);
      const project = await createProject(normalizeProjectPayload(form));
      setForm(emptyProjectForm);
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
      {error && <p className="form-error">{error}</p>}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Создаём" : "Создать проект"}
      </Button>
    </form>
  );
}
