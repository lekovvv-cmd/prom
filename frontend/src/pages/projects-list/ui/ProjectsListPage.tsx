import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { canAcceptProjectResponses } from "../../../entities/project/lib/responseAvailability";
import type { Project, ProjectListParams } from "../../../entities/project/model/types";
import { getProjects } from "../../../entities/project/api/projectApi";
import { ProjectFilters } from "../../../features/filter-projects/ui/ProjectFilters";
import { Header } from "../../../widgets/header/ui/Header";
import { ProjectCardList } from "../../../widgets/project-card-list/ui/ProjectCardList";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";

export function ProjectsListPage() {
  const { user } = useAuth();
  const [filters, setFilters] = useState<ProjectListParams>({ sort: "created_at_desc", limit: 50 });
  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
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

  const selectedProject = projects.find((project) => project.id === selectedProjectId) ?? projects[0] ?? null;
  const currentUserCanRespond = user?.role !== "admin";
  const selectedProjectCanRespond =
    selectedProject && currentUserCanRespond ? canAcceptProjectResponses(selectedProject.status) : false;

  useEffect(() => {
    if (selectedProject && selectedProject.id !== selectedProjectId) {
      setSelectedProjectId(selectedProject.id);
    }
  }, [selectedProject, selectedProjectId]);

  return (
    <>
      <Header />
      <PageLayout
        title="Витрина проектов"
        subtitle={
          <span className="subtitle-lines">
            <span>Найдено проектов: {total}.</span>
            <span>Выберите проект, чтобы быстро проверить цель, ответственного и&nbsp;откликнуться.</span>
          </span>
        }
      >
        <div className="showcase-layout">
          <aside className="filter-rail" aria-label="Фильтры проектов">
            <ProjectFilters value={filters} onChange={setFilters} />
            <div className="rail-note">
              <strong>Сценарий сотрудника</strong>
              <span>Найдите инициативу, откройте детали и отправьте отклик. Статус заявки обновит администратор.</span>
            </div>
          </aside>

          <section className="project-stream" aria-label="Список проектов">
            <div className="stream-toolbar">
              <div>
                <strong>{total}</strong>
                <span>проектов в витрине</span>
              </div>
              <span>Фильтры применяются сразу</span>
            </div>
            {error && <p className="form-error">{error}</p>}
            {isLoading ? (
              <Spinner />
            ) : (
              <ProjectCardList
                projects={projects}
                selectedProjectId={selectedProject?.id}
                onSelect={setSelectedProjectId}
              />
            )}
          </section>

          <aside className="showcase-summary" aria-label="Краткая карточка проекта">
            {selectedProject ? (
              <>
                <div className="summary-kicker">Выбранный проект</div>
                <h2>{selectedProject.title}</h2>
                <p>{selectedProject.short_description}</p>
                <dl className="summary-list">
                  <div>
                    <dt>Цель</dt>
                    <dd>{selectedProject.goal}</dd>
                  </div>
                  <div>
                    <dt>Ответственный</dt>
                    <dd>{selectedProject.responsible?.full_name ?? "Не указан"}</dd>
                  </div>
                  <div>
                    <dt>Отклики</dt>
                    <dd>{selectedProject.responses_count}</dd>
                  </div>
                </dl>
                <div className="summary-actions">
                  {selectedProjectCanRespond ? (
                    <Link className="button button-primary" to={`/projects/${selectedProject.id}#response-form`}>
                      Перейти к отклику
                    </Link>
                  ) : (
                    <Link className="button button-secondary" to={`/projects/${selectedProject.id}`}>
                      Открыть проект
                    </Link>
                  )}
                </div>
              </>
            ) : (
              <p className="muted">Проект не выбран.</p>
            )}
          </aside>
        </div>
      </PageLayout>
    </>
  );
}
