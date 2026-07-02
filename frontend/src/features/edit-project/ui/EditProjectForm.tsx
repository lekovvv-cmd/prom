import { FormEvent, useState } from "react";

import type { ProjectDetails, ProjectMutationPayload } from "../../../entities/project/model/types";
import {
  normalizeProjectPayload,
  ProjectFormFields
} from "../../../entities/project/ui/ProjectFormFields";
import { Button } from "../../../shared/ui/Button";
import { editProject } from "../api/editProject";

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
    responsible_user_id: null,
    contact_email: project.contact_email,
    required_competencies: project.required_competencies,
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
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      setIsSubmitting(true);
      setError(null);
      const updatedProject = await editProject(project.id, normalizeProjectPayload(form));
      onSaved(updatedProject);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось сохранить проект");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="form-panel" onSubmit={handleSubmit}>
      <ProjectFormFields form={form} setForm={setForm} />
      {error && <p className="form-error">{error}</p>}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Сохраняем" : "Сохранить"}
      </Button>
    </form>
  );
}
