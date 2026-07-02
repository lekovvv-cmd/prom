import { MessageSquare, UserRound } from "lucide-react";
import { Link } from "react-router-dom";

import { splitCompetencies } from "../../competency/lib/competencies";
import type { Project } from "../model/types";
import { ProjectPriorityBadge } from "./ProjectPriorityBadge";
import { ProjectStatusBadge } from "./ProjectStatusBadge";
import { formatDate } from "../../../shared/lib/date";
import { Card } from "../../../shared/ui/Card";

export function ProjectCard({
  project,
  isSelected = false,
  onSelect
}: {
  project: Project;
  isSelected?: boolean;
  onSelect?: (projectId: string) => void;
}) {
  const competencies = splitCompetencies(project.required_competencies).slice(0, 4);

  return (
    <Card className={`project-card ${isSelected ? "project-card-selected" : ""}`}>
      <button
        className="project-card-main"
        type="button"
        aria-pressed={isSelected}
        onClick={() => onSelect?.(project.id)}
      >
        <span className="card-topline">
          <ProjectStatusBadge status={project.status} />
          <ProjectPriorityBadge priority={project.priority} />
        </span>
        <span className="project-card-title">{project.title}</span>
        <span className="project-card-description">{project.short_description}</span>
        {competencies.length > 0 && (
          <span className="competency-inline">
            {competencies.map((competency) => (
              <span className="chip" key={competency}>
                {competency}
              </span>
            ))}
          </span>
        )}
        <span className="project-card-goal">{project.goal}</span>
      </button>

      <dl className="project-card-meta">
        <div>
          <dt>Срок</dt>
          <dd>
            {project.start_date ? formatDate(project.start_date) : "Без даты"}
            {project.end_date ? ` - ${formatDate(project.end_date)}` : ""}
          </dd>
        </div>
        <div>
          <dt>Ответственный</dt>
          <dd>
            <UserRound size={15} />
            {project.responsible?.full_name ?? "Не указан"}
          </dd>
        </div>
        <div>
          <dt>Отклики</dt>
          <dd>
            <MessageSquare size={15} />
            {project.responses_count}
          </dd>
        </div>
      </dl>

      <div className="project-card-actions">
        <Link className="button button-secondary" to={`/projects/${project.id}`}>
          Детали
        </Link>
        <Link className="button button-primary" to={`/projects/${project.id}#response-form`}>
          Откликнуться
        </Link>
      </div>
    </Card>
  );
}
