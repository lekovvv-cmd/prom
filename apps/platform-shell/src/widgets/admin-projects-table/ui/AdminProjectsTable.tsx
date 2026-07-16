import { Edit3, FolderKanban } from "lucide-react";
import { Link } from "react-router-dom";

import type { Project } from "../../../entities/project/model/types";
import { ProjectPriorityBadge } from "../../../entities/project/ui/ProjectPriorityBadge";
import { ProjectStatusBadge } from "../../../entities/project/ui/ProjectStatusBadge";
import { ArchiveProjectButton } from "../../../features/archive-project/ui/ArchiveProjectButton";
import { DeleteArchivedProjectButton } from "../../../features/delete-archived-project/ui/DeleteArchivedProjectButton";
import { RestoreArchivedProjectButton } from "../../../features/restore-archived-project/ui/RestoreArchivedProjectButton";
import { formatDateTime } from "../../../shared/lib/date";
import { Button } from "../../../shared/ui/Button";
import { EmptyState } from "../../../shared/ui/EmptyState";
import { Table } from "../../../shared/ui/Table";

export function AdminProjectsTable({
  projects,
  onEdit,
  onArchived,
  isArchiveView = false,
  emptyTitle = "Проектов пока нет",
  emptyText = "Создайте первый проект для витрины."
}: {
  projects: Project[];
  onEdit: (project: Project) => void;
  onArchived: () => void;
  isArchiveView?: boolean;
  emptyTitle?: string;
  emptyText?: string;
}) {
  if (projects.length === 0) {
    return <EmptyState title={emptyTitle} text={emptyText} />;
  }

  return (
    <Table>
      <table>
        <thead>
          <tr>
            <th>Проект</th>
            <th>Статус</th>
            <th>Приоритет</th>
            <th>Отклики</th>
            <th>Создан</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {projects.map((project) => (
            <tr key={project.id}>
              <td>
                <strong>{project.title}</strong>
                <span>{project.short_description}</span>
              </td>
              <td>
                <ProjectStatusBadge status={project.status} />
              </td>
              <td>
                <ProjectPriorityBadge priority={project.priority} />
              </td>
              <td>{project.responses_count}</td>
              <td>{formatDateTime(project.created_at)}</td>
              <td>
                <div className="table-actions">
                  <Link className="button button-secondary" to={`/admin/projects/${project.id}`}>
                    <FolderKanban size={16} />
                    Открыть
                  </Link>
                  <Button variant="secondary" onClick={() => onEdit(project)}>
                    <Edit3 size={16} />
                    Править
                  </Button>
                  {isArchiveView ? (
                    <>
                      <RestoreArchivedProjectButton projectId={project.id} onRestored={onArchived} />
                      <DeleteArchivedProjectButton projectId={project.id} onDeleted={onArchived} />
                    </>
                  ) : project.status !== "archived" ? (
                    <ArchiveProjectButton projectId={project.id} onArchived={onArchived} />
                  ) : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Table>
  );
}
