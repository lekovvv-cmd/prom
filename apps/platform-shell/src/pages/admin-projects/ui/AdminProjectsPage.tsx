import { Plus } from "lucide-react";
import { useEffect, useState } from "react";

import { getAdminProject, getAdminProjects } from "../../../entities/project/api/projectApi";
import type { Project, ProjectDetails, ProjectListParams } from "../../../entities/project/model/types";
import { CreateProjectForm } from "../../../features/create-project/ui/CreateProjectForm";
import { EditProjectForm } from "../../../features/edit-project/ui/EditProjectForm";
import { ProjectFilters } from "../../../features/filter-projects/ui/ProjectFilters";
import { AdminProjectsTable } from "../../../widgets/admin-projects-table/ui/AdminProjectsTable";
import { Header } from "../../../widgets/header/ui/Header";
import { Button } from "../../../shared/ui/Button";
import { Modal } from "../../../shared/ui/Modal";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";

export type AdminProjectsView = "current" | "archive";

export function getAdminProjectListParams(view: AdminProjectsView, filters: ProjectListParams): ProjectListParams {
  if (view === "archive") {
    return { ...filters, status: "archived" };
  }

  if (filters.status === "archived") {
    return { ...filters, status: "" };
  }

  return filters;
}

export function AdminProjectsPage() {
  const [filters, setFilters] = useState<ProjectListParams>({ sort: "created_at_desc", limit: 100 });
  const [view, setView] = useState<AdminProjectsView>("current");
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectTotals, setProjectTotals] = useState({ current: 0, archive: 0 });
  const [editingProject, setEditingProject] = useState<ProjectDetails | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadProjects() {
    try {
      setIsLoading(true);
      setError(null);
      const [response, currentCounter, archiveCounter] = await Promise.all([
        getAdminProjects(getAdminProjectListParams(view, filters)),
        getAdminProjects(getAdminProjectListParams("current", filters)),
        getAdminProjects(getAdminProjectListParams("archive", filters))
      ]);
      setProjects(response.items);
      setProjectTotals({ current: currentCounter.total, archive: archiveCounter.total });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить проекты");
    } finally {
      setIsLoading(false);
    }
  }

  async function openEdit(project: Project) {
    try {
      const details = await getAdminProject(project.id);
      setEditingProject(details);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось открыть проект");
    }
  }

  useEffect(() => {
    void loadProjects();
  }, [filters, view]);

  return (
    <>
      <Header />
      <PageLayout
        title="Управление проектами"
        actions={
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus size={18} />
            Создать проект
          </Button>
        }
      >
        <div className="view-tabs" role="tablist" aria-label="Раздел проектов">
          <Button
            aria-selected={view === "current"}
            onClick={() => setView("current")}
            role="tab"
            type="button"
            variant={view === "current" ? "primary" : "secondary"}
          >
            Текущие
          </Button>
          <Button
            aria-selected={view === "archive"}
            onClick={() => setView("archive")}
            role="tab"
            type="button"
            variant={view === "archive" ? "primary" : "secondary"}
          >
            Архив
          </Button>
        </div>
        <div className="project-counter-strip" aria-label="Счётчики проектов">
          <div>
            <span>Текущие</span>
            <strong>{projectTotals.current}</strong>
          </div>
          <div>
            <span>Архив</span>
            <strong>{projectTotals.archive}</strong>
          </div>
          <div>
            <span>Всего</span>
            <strong>{projectTotals.current + projectTotals.archive}</strong>
          </div>
        </div>
        <ProjectFilters value={filters} onChange={setFilters} includeDraft hideStatus={view === "archive"} />
        {error && <p className="form-error">{error}</p>}
        {isLoading ? (
          <Spinner />
        ) : (
          <AdminProjectsTable
            projects={projects}
            onEdit={openEdit}
            onArchived={loadProjects}
            isArchiveView={view === "archive"}
            emptyTitle={view === "archive" ? "Архив пуст" : "Проектов пока нет"}
            emptyText={
              view === "archive"
                ? "Архивированные проекты появятся здесь после нажатия кнопки «Архив»."
                : "Создайте первый проект для витрины."
            }
          />
        )}
      </PageLayout>

      {isCreateOpen && (
        <Modal title="Создать проект" onClose={() => setIsCreateOpen(false)}>
          <CreateProjectForm
            onCreated={() => {
              setIsCreateOpen(false);
              void loadProjects();
            }}
          />
        </Modal>
      )}

      {editingProject && (
        <Modal title="Редактировать проект" onClose={() => setEditingProject(null)}>
          <EditProjectForm
            project={editingProject}
            onSaved={() => {
              setEditingProject(null);
              void loadProjects();
            }}
          />
        </Modal>
      )}
    </>
  );
}
