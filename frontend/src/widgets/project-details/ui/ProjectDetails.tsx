import type { ReactNode } from "react";

import type { ProjectDetails as ProjectDetailsType } from "../../../entities/project/model/types";
import { AttachmentList } from "../../../entities/attachment/ui/AttachmentList";
import { normalizeCompetencyBlocks } from "../../../entities/competency/lib/competencyBlocks";
import { CompetencyCoverage } from "../../../entities/competency/ui/CompetencyCoverage";
import { splitProjectTasks } from "../../../entities/project/lib/projectTasks";
import { canAcceptProjectResponses } from "../../../entities/project/lib/responseAvailability";
import { ProjectPriorityBadge } from "../../../entities/project/ui/ProjectPriorityBadge";
import { ProjectStatusBadge } from "../../../entities/project/ui/ProjectStatusBadge";
import { ProjectResponseForm } from "../../../features/submit-project-response/ui/ProjectResponseForm";
import { formatDate } from "../../../shared/lib/date";
import { Card } from "../../../shared/ui/Card";

export function ProjectDetails({
  project,
  onResponseSubmitted = () => undefined,
  showResponseForm = true,
  participationNotice
}: {
  project: ProjectDetailsType;
  onResponseSubmitted?: () => void;
  showResponseForm?: boolean;
  participationNotice?: ReactNode;
}) {
  const competencyBlocks = normalizeCompetencyBlocks(project.competency_blocks, project.required_competencies);
  const plannedTasks = splitProjectTasks(project.planned_tasks);
  const canRespond = canAcceptProjectResponses(project.status);
  const workingGroup = project.members.filter((member) => member.member_role === "working_group_member");

  return (
    <div className="details-layout">
      <section className="details-main">
        <div className="details-heading">
          <div className="card-topline">
            <ProjectStatusBadge status={project.status} />
            <ProjectPriorityBadge priority={project.priority} />
          </div>
          <h2>{project.title}</h2>
          <p>{project.short_description}</p>
        </div>
        <Card>
          <h3>Описание</h3>
          <p>{project.description}</p>
        </Card>
        <Card>
          <h3>Цель</h3>
          <p>{project.goal}</p>
        </Card>
        {project.expected_result && (
          <Card>
            <h3>Ожидаемый результат</h3>
            <p>{project.expected_result}</p>
          </Card>
        )}
        {(competencyBlocks.length > 0 || plannedTasks.length > 0) && (
          <Card>
            {competencyBlocks.length > 0 && (
              <div className="details-section">
                <h3>Направления работы</h3>
                <CompetencyCoverage blocks={competencyBlocks} coverage={project.competency_coverage} />
              </div>
            )}
            {plannedTasks.length > 0 && (
              <div className="details-section">
                <h3>Планируемые задачи</h3>
                <ol className="task-list">
                  {plannedTasks.map((task, index) => (
                    <li key={`${task}-${index}`}>{task}</li>
                  ))}
                </ol>
              </div>
            )}
          </Card>
        )}
      </section>
      <aside className="details-side">
        {!showResponseForm ? (
          <Card>
            <h3>Ваше участие</h3>
            {participationNotice ?? (
              <p className="muted">Проект доступен вам как участнику. Здесь можно смотреть параметры, задачи и материалы.</p>
            )}
          </Card>
        ) : canRespond ? (
          <ProjectResponseForm projectId={project.id} onSubmitted={onResponseSubmitted} />
        ) : (
          <Card>
            <h3>Отклики закрыты</h3>
            <p className="muted">Новые отклики доступны только для активных и приостановленных проектов.</p>
          </Card>
        )}
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
              <dt>Отклики</dt>
              <dd>{project.responses_count}</dd>
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
      </aside>
    </div>
  );
}
