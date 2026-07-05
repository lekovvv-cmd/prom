import { Edit3, FolderKanban } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AttachmentList } from "../../../entities/attachment/ui/AttachmentList";
import { normalizeCompetencyBlocks } from "../../../entities/competency/lib/competencyBlocks";
import { CompetencyCoverage } from "../../../entities/competency/ui/CompetencyCoverage";
import { getAdminProject } from "../../../entities/project/api/projectApi";
import { splitProjectTasks } from "../../../entities/project/lib/projectTasks";
import type { ProjectDetails } from "../../../entities/project/model/types";
import { ProjectPriorityBadge } from "../../../entities/project/ui/ProjectPriorityBadge";
import { ProjectStatusBadge } from "../../../entities/project/ui/ProjectStatusBadge";
import { getAdminProjectResponses } from "../../../entities/project-response/api/projectResponseApi";
import type { ProjectResponse } from "../../../entities/project-response/model/types";
import { ArchiveProjectButton } from "../../../features/archive-project/ui/ArchiveProjectButton";
import { DeleteArchivedProjectButton } from "../../../features/delete-archived-project/ui/DeleteArchivedProjectButton";
import { EditProjectForm } from "../../../features/edit-project/ui/EditProjectForm";
import { RestoreArchivedProjectButton } from "../../../features/restore-archived-project/ui/RestoreArchivedProjectButton";
import { AdminResponsesTable } from "../../../widgets/admin-responses-table/ui/AdminResponsesTable";
import { Header } from "../../../widgets/header/ui/Header";
import { formatDate, formatDateTime } from "../../../shared/lib/date";
import { Button } from "../../../shared/ui/Button";
import { Card } from "../../../shared/ui/Card";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Modal } from "../../../shared/ui/Modal";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";

export function getProjectManagementMetrics(project: ProjectDetails, responses: ProjectResponse[]) {
  const workingGroupSize = project.members.filter((member) => member.member_role === "working_group_member").length;
  const newResponses = responses.filter((response) => response.status === "new").length;
  const acceptedResponses = responses.filter((response) => response.status === "accepted").length;
  const activeQueue = responses.filter((response) =>
    ["new", "viewed", "contacted"].includes(response.status)
  ).length;

  return {
    totalResponses: project.responses_count,
    newResponses,
    acceptedResponses,
    activeQueue,
    workingGroupSize,
    projectFiles: project.attachments.length
  };
}

export function AdminProjectManagePage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState<ProjectDetails | null>(null);
  const [responses, setResponses] = useState<ProjectResponse[]>([]);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProject = useCallback(async () => {
    if (!projectId) {
      setError("Проект не найден");
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const [projectDetails, projectResponses] = await Promise.all([
        getAdminProject(projectId),
        getAdminProjectResponses(projectId, { limit: 100 })
      ]);
      setProject(projectDetails);
      setResponses(projectResponses.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить проект");
      setProject(null);
      setResponses([]);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  const competencyBlocks = useMemo(
    () => normalizeCompetencyBlocks(project?.competency_blocks, project?.required_competencies),
    [project?.competency_blocks, project?.required_competencies]
  );
  const plannedTasks = useMemo(() => splitProjectTasks(project?.planned_tasks), [project?.planned_tasks]);
  const workingGroup = useMemo(
    () => project?.members.filter((member) => member.member_role === "working_group_member") ?? [],
    [project?.members]
  );
  const metrics = useMemo(
    () => (project ? getProjectManagementMetrics(project, responses) : null),
    [project, responses]
  );

  const title = project?.title ?? "Управление проектом";

  return (
    <>
      <Header />
      <PageLayout
        title={title}
        subtitle="Рабочее место руководителя: параметры, материалы, команда и отклики по выбранному проекту."
        actions={
          <Link className="button button-secondary" to="/admin/projects">
            Назад к проектам
          </Link>
        }
      >
        {error && <p className="form-error">{error}</p>}
        {isLoading ? (
          <Spinner />
        ) : !project ? (
          <EmptyState title="Проект не найден" text="Проверьте ссылку или права доступа к проекту." />
        ) : (
          <div className="project-management-page">
            <section className="project-management-hero" aria-label="Сводка проекта">
              <div>
                <div className="card-topline">
                  <ProjectStatusBadge status={project.status} />
                  <ProjectPriorityBadge priority={project.priority} />
                </div>
                <h2>{project.title}</h2>
                <p>{project.short_description}</p>
              </div>
              <div className="management-toolbar">
                <Button variant="secondary" onClick={() => setIsEditOpen(true)}>
                  <Edit3 size={16} />
                  Править
                </Button>
                {project.status === "archived" ? (
                  <>
                    <RestoreArchivedProjectButton projectId={project.id} onRestored={loadProject} />
                    <DeleteArchivedProjectButton
                      projectId={project.id}
                      onDeleted={() => navigate("/admin/projects")}
                    />
                  </>
                ) : (
                  <ArchiveProjectButton projectId={project.id} onArchived={loadProject} />
                )}
              </div>
            </section>

            {metrics && (
              <section className="project-management-metrics" aria-label="Показатели проекта">
                <Card className="metric-card">
                  <span>Всего откликов</span>
                  <strong>{metrics.totalResponses}</strong>
                </Card>
                <Card className="metric-card">
                  <span>Новые</span>
                  <strong>{metrics.newResponses}</strong>
                </Card>
                <Card className="metric-card">
                  <span>В работе</span>
                  <strong>{metrics.activeQueue}</strong>
                </Card>
                <Card className="metric-card">
                  <span>Приняты</span>
                  <strong>{metrics.acceptedResponses}</strong>
                </Card>
              </section>
            )}

            <div className="project-management-grid">
              <section className="project-management-main">
                <Card>
                  <div className="section-heading">
                    <h3>Описание и цель</h3>
                    <span>Обновлено {formatDateTime(project.updated_at)}</span>
                  </div>
                  <div className="details-section">
                    <h4>Описание</h4>
                    <p>{project.description}</p>
                  </div>
                  <div className="details-section">
                    <h4>Цель</h4>
                    <p>{project.goal}</p>
                  </div>
                  {project.expected_result && (
                    <div className="details-section">
                      <h4>Ожидаемый результат</h4>
                      <p>{project.expected_result}</p>
                    </div>
                  )}
                </Card>

                {(competencyBlocks.length > 0 || plannedTasks.length > 0) && (
                  <Card>
                    <div className="section-heading">
                      <h3>Компетенции и задачи</h3>
                    </div>
                    {competencyBlocks.length > 0 && (
                      <div className="details-section">
                        <h4>Направления работы</h4>
                        <CompetencyCoverage blocks={competencyBlocks} coverage={project.competency_coverage} />
                      </div>
                    )}
                    {plannedTasks.length > 0 && (
                      <div className="details-section">
                        <h4>Планируемые задачи</h4>
                        <ol className="task-list">
                          {plannedTasks.map((task, index) => (
                            <li key={`${task}-${index}`}>{task}</li>
                          ))}
                        </ol>
                      </div>
                    )}
                  </Card>
                )}

                <Card className="project-responses-section">
                  <div className="section-heading">
                    <div>
                      <h3>Отклики по проекту</h3>
                      <p className="muted">Руководитель видит и обрабатывает только отклики своего проекта.</p>
                    </div>
                    <span>{responses.length} из {project.responses_count}</span>
                  </div>
                  <AdminResponsesTable responses={responses} onUpdated={loadProject} />
                </Card>
              </section>

              <aside className="project-management-side">
                <Card>
                  <h3>Параметры</h3>
                  <dl className="side-list">
                    <div>
                      <dt>Ответственный</dt>
                      <dd>{project.responsible?.full_name ?? "Не указан"}</dd>
                    </div>
                    <div>
                      <dt>Контакт</dt>
                      <dd>{project.contact_email ?? project.responsible?.email ?? "Не указан"}</dd>
                    </div>
                    <div>
                      <dt>Сроки</dt>
                      <dd>
                        {formatDate(project.start_date)}
                        {project.end_date ? ` - ${formatDate(project.end_date)}` : ""}
                      </dd>
                    </div>
                    <div>
                      <dt>Файлы</dt>
                      <dd>{metrics?.projectFiles ?? 0}</dd>
                    </div>
                    <div>
                      <dt>Рабочая группа</dt>
                      <dd>{metrics?.workingGroupSize ?? 0}</dd>
                    </div>
                  </dl>
                </Card>

                <Card>
                  <h3>Файлы проекта</h3>
                  <AttachmentList attachments={project.attachments} />
                </Card>

                <Card>
                  <h3>Рабочая группа</h3>
                  {workingGroup.length === 0 ? (
                    <p className="muted">Пока не указана.</p>
                  ) : (
                    <ul className="member-list">
                      {workingGroup.map((member) => (
                        <li key={member.id}>
                          <strong>{member.full_name}</strong>
                          <span>{member.email}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Card>

                <Card>
                  <h3>Быстрый переход</h3>
                  {project.status === "draft" || project.status === "archived" ? (
                    <p className="muted">Публичная страница недоступна для черновиков и архивных проектов.</p>
                  ) : (
                    <Link className="button button-secondary" to={`/projects/${project.id}`}>
                      <FolderKanban size={16} />
                      Открыть публичную страницу
                    </Link>
                  )}
                </Card>
              </aside>
            </div>
          </div>
        )}
      </PageLayout>

      {project && isEditOpen && (
        <Modal title="Редактировать проект" onClose={() => setIsEditOpen(false)}>
          <EditProjectForm
            project={project}
            onSaved={() => {
              setIsEditOpen(false);
              void loadProject();
            }}
          />
        </Modal>
      )}
    </>
  );
}
