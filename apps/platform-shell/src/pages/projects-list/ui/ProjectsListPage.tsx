import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import type { Project, ProjectListParams, ProjectRecommendation } from "../../../entities/project/model/types";
import { getProjectRecommendations, getProjects } from "../../../entities/project/api/projectApi";
import { ProjectFilters } from "../../../features/filter-projects/ui/ProjectFilters";
import { Header } from "../../../widgets/header/ui/Header";
import { ProjectCardList } from "../../../widgets/project-card-list/ui/ProjectCardList";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";

export function ProjectsListPage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState<ProjectListParams>({ sort: "created_at_desc", limit: 50 });
  const [projects, setProjects] = useState<Project[]>([]);
  const [recommendations, setRecommendations] = useState<ProjectRecommendation[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const canLoadRecommendations = Boolean(token && user?.role !== "platform_admin");

  useEffect(() => {
    let ignore = false;
    async function loadProjects() {
      try {
        setIsLoading(true);
        setError(null);
        const [response, recommendedProjects] = await Promise.all([
          getProjects(filters),
          canLoadRecommendations ? getProjectRecommendations(5) : Promise.resolve([])
        ]);
        if (!ignore) {
          setProjects(response.items);
          setRecommendations(recommendedProjects);
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
  }, [canLoadRecommendations, filters]);

  const visibleRecommendations = useMemo(() => {
    const projectIds = new Set(projects.map((project) => project.id));
    return recommendations.filter((item) => projectIds.has(item.project.id));
  }, [projects, recommendations]);

  return (
    <>
      <Header />
      <PageLayout title="Витрина проектов">
        <div className="showcase-layout">
          <aside className="filter-rail" aria-label="Фильтры проектов">
            <ProjectFilters value={filters} onChange={setFilters} />
          </aside>

          <section className="project-stream" aria-label="Список проектов">
            <div className="stream-toolbar">
              <div>
                <strong>{total}</strong>
                <span>проектов в витрине</span>
              </div>
            </div>
            {visibleRecommendations.length > 0 && (
              <ProjectRecommendations recommendations={visibleRecommendations} />
            )}
            {error && <p className="form-error">{error}</p>}
            {isLoading ? <Spinner /> : <ProjectCardList projects={projects} />}
          </section>
        </div>
      </PageLayout>
    </>
  );
}

function ProjectRecommendations({ recommendations }: { recommendations: ProjectRecommendation[] }) {
  return (
    <section className="recommendation-panel" aria-label="Рекомендуем вам">
      <div className="section-heading">
        <h2>Рекомендуем вам</h2>
      </div>
      <div className="recommendation-list">
        {recommendations.map((recommendation) => {
          const matchCount =
            recommendation.matched_competencies.length +
            recommendation.matched_blocks.length +
            recommendation.matched_profile_terms.length;
          return (
            <Link
              className="recommendation-card"
              to={`/projects/${recommendation.project.id}`}
              key={recommendation.project.id}
            >
              <span className="summary-kicker">Совпадение по вашему профилю</span>
              <strong>{recommendation.project.title}</strong>
              {recommendation.matched_competencies.length > 0 && (
                <span className="recommendation-reason">
                  Совпадают компетенции: {recommendation.matched_competencies.slice(0, 4).join(", ")}
                </span>
              )}
              {recommendation.matched_blocks.length > 0 && (
                <span className="recommendation-reason">
                  Направления: {recommendation.matched_blocks.slice(0, 3).join(", ")}
                </span>
              )}
              <span className="recommendation-score">{matchCount} совпадений по профилю</span>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
