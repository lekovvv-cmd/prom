import { MessageSquare, UserRound } from "lucide-react";
import { Link } from "react-router-dom";

import type { Project } from "../model/types";
import { ProjectPriorityBadge } from "./ProjectPriorityBadge";
import { ProjectStatusBadge } from "./ProjectStatusBadge";
import { formatDate } from "../../../shared/lib/date";
import { Card } from "../../../shared/ui/Card";

export function ProjectCard({ project }: { project: Project }) {
  return (
    <Card className="project-card">
      <div className="card-topline">
        <ProjectStatusBadge status={project.status} />
        <ProjectPriorityBadge priority={project.priority} />
      </div>
      <h2>{project.title}</h2>
      <p>{project.short_description}</p>
      <dl className="meta-grid">
        <div>
          <dt>Цель</dt>
          <dd>{project.goal}</dd>
        </div>
        <div>
          <dt>Срок</dt>
          <dd>
            {project.start_date ? formatDate(project.start_date) : "Без даты"}
            {project.end_date ? ` - ${formatDate(project.end_date)}` : ""}
          </dd>
        </div>
      </dl>
      <div className="card-footer">
        <span className="inline-meta">
          <UserRound size={16} />
          {project.responsible?.full_name ?? "Ответственный не указан"}
        </span>
        <span className="inline-meta">
          <MessageSquare size={16} />
          {project.responses_count}
        </span>
      </div>
      <div className="button-row">
        <Link className="button button-secondary" to={`/projects/${project.id}`}>
          Подробнее
        </Link>
        <Link className="button button-primary" to={`/projects/${project.id}#response-form`}>
          Откликнуться
        </Link>
      </div>
    </Card>
  );
}
