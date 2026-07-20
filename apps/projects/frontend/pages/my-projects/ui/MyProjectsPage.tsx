import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { getMyProjects } from "../../../entities/project/api/projectApi";
import type {
  ProjectListParams,
  ProjectStatus,
} from "../../../entities/project/model/types";
import { projectsQueryKeys } from "../../../api/queryKeys";
import { ProjectCard } from "../../../entities/project/ui/ProjectCard";
import { Header } from "@prom/layout";
import { EmptyState } from "@prom/ui/EmptyState";
import { Input } from "@prom/ui/Input";
import { PageLayout } from "@prom/ui/PageLayout";
import { Select } from "@prom/ui/Select";
import { Spinner } from "@prom/ui/Spinner";

export function MyProjectsPage() {
  const [filters, setFilters] = useState<ProjectListParams>({
    limit: 100,
    sort: "created_at_desc",
  });
  const projectsQuery = useQuery({
    queryKey: projectsQueryKeys.myList(filters),
    queryFn: ({ signal }) => getMyProjects(filters, signal),
  });
  const projects = projectsQuery.data?.items ?? [];
  const total = projectsQuery.data?.total ?? 0;
  const error =
    projectsQuery.error instanceof Error ? projectsQuery.error.message : null;

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
            onChange={(event) =>
              updateFilter({ status: event.target.value as ProjectStatus | "" })
            }
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
            onChange={(event) =>
              updateFilter({
                sort: event.target.value as ProjectListParams["sort"],
              })
            }
          >
            <option value="created_at_desc">Новые сначала</option>
            <option value="created_at_asc">Старые сначала</option>
            <option value="priority_desc">Высокий приоритет</option>
            <option value="priority_asc">Низкий приоритет</option>
          </Select>
        </div>
        {error && <p className="form-error">{error}</p>}
        {projectsQuery.isLoading ? (
          <Spinner />
        ) : projects.length === 0 ? (
          <EmptyState title="Проектов пока нет" />
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
