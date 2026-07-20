import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@prom/auth";
import type {
  ProjectListParams,
  ProjectRecommendation,
} from "../../../entities/project/model/types";
import {
  getProjectRecommendations,
  getProjects,
} from "../../../entities/project/api/projectApi";
import { projectsQueryKeys } from "../../../api/queryKeys";
import { ProjectFilters } from "../../../features/filter-projects/ui/ProjectFilters";
import { Header } from "@prom/layout";
import { ProjectCardList } from "../../../widgets/project-card-list/ui/ProjectCardList";
import { PageLayout } from "@prom/ui/PageLayout";
import { Spinner } from "@prom/ui/Spinner";

export function ProjectsListPage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState<ProjectListParams>({
    sort: "created_at_desc",
    limit: 50,
  });
  const canLoadRecommendations = Boolean(
    token && user?.role !== "platform_admin",
  );
  const projectsQuery = useQuery({
    queryKey: projectsQueryKeys.showcase(filters, canLoadRecommendations),
    queryFn: async ({ signal }) => {
      const [response, recommendations] = await Promise.all([
        getProjects(filters, signal),
        canLoadRecommendations
          ? getProjectRecommendations(5, signal)
          : Promise.resolve([]),
      ]);
      return { response, recommendations };
    },
  });
  const projects = projectsQuery.data?.response.items ?? [];
  const recommendations = projectsQuery.data?.recommendations ?? [];
  const total = projectsQuery.data?.response.total ?? 0;
  const error =
    projectsQuery.error instanceof Error ? projectsQuery.error.message : null;

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
              <ProjectRecommendations
                recommendations={visibleRecommendations}
              />
            )}
            {error && <p className="form-error">{error}</p>}
            {projectsQuery.isLoading ? (
              <Spinner />
            ) : (
              <ProjectCardList projects={projects} />
            )}
          </section>
        </div>
      </PageLayout>
    </>
  );
}

function ProjectRecommendations({
  recommendations,
}: {
  recommendations: ProjectRecommendation[];
}) {
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
              <span className="summary-kicker">
                Совпадение по вашему профилю
              </span>
              <strong>{recommendation.project.title}</strong>
              {recommendation.matched_competencies.length > 0 && (
                <span className="recommendation-reason">
                  Совпадают компетенции:{" "}
                  {recommendation.matched_competencies.slice(0, 4).join(", ")}
                </span>
              )}
              {recommendation.matched_blocks.length > 0 && (
                <span className="recommendation-reason">
                  Направления:{" "}
                  {recommendation.matched_blocks.slice(0, 3).join(", ")}
                </span>
              )}
              <span className="recommendation-score">
                {matchCount} совпадений по профилю
              </span>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
