import { useEffect, useState } from "react";

import type { Project, ProjectListParams } from "../../../entities/project/model/types";
import { getProjects } from "../../../entities/project/api/projectApi";
import { ProjectFilters } from "../../../features/filter-projects/ui/ProjectFilters";
import { Header } from "../../../widgets/header/ui/Header";
import { ProjectCardList } from "../../../widgets/project-card-list/ui/ProjectCardList";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";

export function ProjectsListPage() {
  const [filters, setFilters] = useState<ProjectListParams>({ sort: "created_at_desc", limit: 50 });
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let ignore = false;
    async function loadProjects() {
      try {
        setIsLoading(true);
        setError(null);
        const response = await getProjects(filters);
        if (!ignore) {
          setProjects(response.items);
          setTotal(response.total);
        }
      } catch (err) {
        if (!ignore) {
          setError(err instanceof Error ? err.message : "Не удалось загрузить проекты");
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }
    void loadProjects();
    return () => {
      ignore = true;
    };
  }, [filters]);

  return (
    <>
      <Header />
      <PageLayout
        title="Проекты"
        subtitle={`Витрина стратегических проектов. Найдено: ${total}`}
      >
        <ProjectFilters value={filters} onChange={setFilters} />
        {error && <p className="form-error">{error}</p>}
        {isLoading ? <Spinner /> : <ProjectCardList projects={projects} />}
      </PageLayout>
    </>
  );
}
