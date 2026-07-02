import type { ProjectDetails as ProjectDetailsType } from "../../../entities/project/model/types";
import { AttachmentList } from "../../../entities/attachment/ui/AttachmentList";
import { splitCompetencies } from "../../../entities/competency/lib/competencies";
import { ProjectPriorityBadge } from "../../../entities/project/ui/ProjectPriorityBadge";
import { ProjectStatusBadge } from "../../../entities/project/ui/ProjectStatusBadge";
import { ProjectResponseForm } from "../../../features/submit-project-response/ui/ProjectResponseForm";
import { formatDate } from "../../../shared/lib/date";
import { Card } from "../../../shared/ui/Card";

export function ProjectDetails({
  project,
  onResponseSubmitted
}: {
  project: ProjectDetailsType;
  onResponseSubmitted: () => void;
}) {
  const competencies = splitCompetencies(project.required_competencies);

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
        {(project.required_competencies || project.planned_tasks) && (
          <Card>
            {project.required_competencies && (
              <>
                <h3>Требуемые компетенции</h3>
                <div className="competency-inline">
                  {competencies.map((competency) => (
                    <span className="chip chip-selected" key={competency}>
                      {competency}
                    </span>
                  ))}
                </div>
              </>
            )}
            {project.planned_tasks && (
              <>
                <h3>Планируемые задачи</h3>
                <p>{project.planned_tasks}</p>
              </>
            )}
          </Card>
        )}
      </section>
      <aside className="details-side">
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
          {project.members.length === 0 ? (
            <p className="muted">Пока не указана.</p>
          ) : (
            <ul className="member-list">
              {project.members.map((member) => (
                <li key={member.id}>
                  <strong>{member.full_name}</strong>
                  <span>{member.email}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <ProjectResponseForm projectId={project.id} onSubmitted={onResponseSubmitted} />
      </aside>
    </div>
  );
}
