import { useEffect, useState } from "react";

import { getMyProjects } from "../../../entities/project/api/projectApi";
import type { Project, ProjectListParams, ProjectStatus } from "../../../entities/project/model/types";
import { ProjectCard } from "../../../entities/project/ui/ProjectCard";
import { Header } from "../../../widgets/header/ui/Header";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Select } from "../../../shared/ui/Select";
import { Spinner } from "../../../shared/ui/Spinner";

export function MyProjectsPage() {
  const [filters, setFilters] = useState<ProjectListParams>({ limit: 100, sort: "created_at_desc" });
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadProjects() {
    try {
      setIsLoading(true);
      setError(null);
      const payload = await getMyProjects(filters);
      setProjects(payload.items);
      setTotal(payload.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить ваши проекты");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadProjects();
  }, [filters]);

  function updateFilter(nextFilters: Partial<ProjectListParams>) {
    setFilters((current) => ({ ...current, ...nextFilters, offset: 0 }));
  }

  return (
    <>
      <Header />
      <PageLayout title="Мои проекты">
        <div className="filters my-projects-filters">
          <Input
            label="Поиск"
            name="search"
            value={filters.search ?? ""}
            onChange={(event) => updateFilter({ search: event.target.value })}
            placeholder="Название проекта"
          />
          <Select
            label="Статус"
            name="status"
            value={filters.status ?? ""}
            isClearable
            clearLabel="Сбросить фильтр по статусу"
            onClear={() => updateFilter({ status: "" })}
            onChange={(event) => updateFilter({ status: event.target.value as ProjectStatus | "" })}
          >
            <option value="" disabled hidden>
              Все статусы
            </option>
            <option value="active">Активен</option>
            <option value="paused">Пауза</option>
            <option value="completed">Завершён</option>
            <option value="archived">Архив</option>
          </Select>
          <Select
            label="Сортировка"
            name="sort"
            value={filters.sort ?? "created_at_desc"}
            onChange={(event) => updateFilter({ sort: event.target.value as ProjectListParams["sort"] })}
          >
            <option value="created_at_desc">Новые сначала</option>
            <option value="created_at_asc">Старые сначала</option>
            <option value="priority_desc">Высокий приоритет</option>
            <option value="priority_asc">Низкий приоритет</option>
          </Select>
        </div>
        {error && <p className="form-error">{error}</p>}
        {isLoading ? (
          <Spinner />
        ) : projects.length === 0 ? (
          <EmptyState
            title="Проектов пока нет"
          />
        ) : (
          <section className="project-stream my-projects-stream">
            <div className="stream-toolbar">
              <div>
                <strong>{total}</strong>
                <span>проектов</span>
              </div>
            </div>
            <div className="project-list">
              {projects.map((project) => (
                <ProjectCard
                  detailsPath={`/my/projects/${project.id}`}
                  key={project.id}
                  project={project}
                />
              ))}
            </div>
          </section>
        )}
      </PageLayout>
    </>
  );
}
