import { useEffect, useState } from "react";

import { getAdminProjects } from "../../../entities/project/api/projectApi";
import type { Project } from "../../../entities/project/model/types";
import { getAdminResponses } from "../../../entities/project-response/api/projectResponseApi";
import type { ProjectResponse, ProjectResponseStatus } from "../../../entities/project-response/model/types";
import { AdminResponsesTable } from "../../../widgets/admin-responses-table/ui/AdminResponsesTable";
import { Header } from "../../../widgets/header/ui/Header";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";

export function AdminResponsesPage() {
  const [responses, setResponses] = useState<ProjectResponse[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [status, setStatus] = useState<ProjectResponseStatus | "">("");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadResponses() {
    try {
      setIsLoading(true);
      setError(null);
      const [responsesPayload, projectsPayload] = await Promise.all([
        getAdminResponses({ project_id: projectId, status, search, limit: 100 }),
        getAdminProjects({ limit: 100 })
      ]);
      setResponses(responsesPayload.items);
      setProjects(projectsPayload.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить отклики");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadResponses();
  }, [projectId, status, search]);

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
          <Select
            label="Проект"
            name="project_id"
            value={projectId}
            isClearable
            clearLabel="Сбросить фильтр по проекту"
            onClear={() => setProjectId("")}
            onChange={(event) => setProjectId(event.target.value)}
          >
            <option value="" disabled hidden>
              Проект не выбран
            </option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.title}
              </option>
            ))}
          </Select>
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
