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

export function AdminProjectsPage() {
  const [filters, setFilters] = useState<ProjectListParams>({ sort: "created_at_desc", limit: 100 });
  const [projects, setProjects] = useState<Project[]>([]);
  const [editingProject, setEditingProject] = useState<ProjectDetails | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadProjects() {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getAdminProjects(filters);
      setProjects(response.items);
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
  }, [filters]);

  return (
    <>
      <Header />
      <PageLayout
        title="Админка проектов"
        subtitle="Создание, редактирование и архивирование проектов"
        actions={
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus size={18} />
            Создать проект
          </Button>
        }
      >
        <ProjectFilters value={filters} onChange={setFilters} includeArchived />
        {error && <p className="form-error">{error}</p>}
        {isLoading ? (
          <Spinner />
        ) : (
          <AdminProjectsTable projects={projects} onEdit={openEdit} onArchived={loadProjects} />
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
