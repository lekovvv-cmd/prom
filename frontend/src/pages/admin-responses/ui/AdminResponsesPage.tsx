import { useEffect, useMemo, useState } from "react";

import { getAdminProjects } from "../../../entities/project/api/projectApi";
import type { Project } from "../../../entities/project/model/types";
import { getAdminResponses } from "../../../entities/project-response/api/projectResponseApi";
import type { ProjectResponse, ProjectResponseStatus } from "../../../entities/project-response/model/types";
import { AdminResponsesTable } from "../../../widgets/admin-responses-table/ui/AdminResponsesTable";
import { Header } from "../../../widgets/header/ui/Header";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { SearchableSelect } from "../../../shared/ui/SearchableSelect";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";

export function AdminResponsesPage() {
  const [responses, setResponses] = useState<ProjectResponse[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [projectSearch, setProjectSearch] = useState("");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [status, setStatus] = useState<ProjectResponseStatus | "">("");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isProjectsLoading, setIsProjectsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadResponses() {
    try {
      setIsLoading(true);
      setError(null);
      const responsesPayload = await getAdminResponses({ project_id: projectId, status, search, limit: 100 });
      setResponses(responsesPayload.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить отклики");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadProjects(query: string) {
    try {
      setIsProjectsLoading(true);
      const [currentProjectsPayload, archivedProjectsPayload] = await Promise.all([
        getAdminProjects({ search: query, limit: 100 }),
        getAdminProjects({ search: query, status: "archived", limit: 100 })
      ]);
      const uniqueProjects = [...currentProjectsPayload.items, ...archivedProjectsPayload.items].filter(
        (project, index, items) => items.findIndex((item) => item.id === project.id) === index
      );
      setProjects(uniqueProjects);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить проекты");
    } finally {
      setIsProjectsLoading(false);
    }
  }

  useEffect(() => {
    void loadResponses();
  }, [projectId, status, search]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadProjects(projectSearch);
    }, 200);

    return () => window.clearTimeout(timeoutId);
  }, [projectSearch]);

  const projectOptions = useMemo(() => {
    const options = projects.map((project) => ({
      value: project.id,
      label: project.title
    }));
    if (selectedProject && !options.some((option) => option.value === selectedProject.id)) {
      options.unshift({
        value: selectedProject.id,
        label: selectedProject.title
      });
    }
    return options;
  }, [projects, selectedProject]);

  function handleProjectChange(nextProjectId: string) {
    setProjectId(nextProjectId);
    if (!nextProjectId) {
      setSelectedProject(null);
      return;
    }

    const nextProject = projects.find((project) => project.id === nextProjectId) ?? selectedProject;
    setSelectedProject(nextProject?.id === nextProjectId ? nextProject : null);
  }

  return (
    <>
      <Header />
      <PageLayout title="Очередь откликов" subtitle="Обработка заявок сотрудников на участие в проектах">
        <div className="filters">
          <Input
            label="Поиск"
            name="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="ФИО или email"
          />
          <SearchableSelect
            label="Проект"
            name="project_id"
            value={projectId}
            options={projectOptions}
            isLoading={isProjectsLoading}
            placeholder="Проект не выбран"
            searchPlaceholder="Название проекта"
            emptyText="Проекты не найдены"
            clearLabel="Сбросить фильтр по проекту"
            onChange={handleProjectChange}
            onSearchChange={setProjectSearch}
          />
          <Select
            label="Статус"
            name="status"
            value={status}
            isClearable
            clearLabel="Сбросить фильтр по статусу"
            onClear={() => setStatus("")}
            onChange={(event) => setStatus(event.target.value as ProjectResponseStatus | "")}
          >
            <option value="" disabled hidden>
              Статус не выбран
            </option>
            <option value="new">Новый</option>
            <option value="viewed">Просмотрен</option>
            <option value="contacted">Связались</option>
            <option value="accepted">Принят</option>
            <option value="rejected">Отклонён</option>
            <option value="cancelled">Отозван</option>
          </Select>
        </div>
        {error && <p className="form-error">{error}</p>}
        {isLoading ? <Spinner /> : <AdminResponsesTable responses={responses} onUpdated={loadResponses} />}
      </PageLayout>
    </>
  );
}
