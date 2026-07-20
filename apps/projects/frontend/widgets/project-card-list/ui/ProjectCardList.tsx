import type { Project } from "../../../entities/project/model/types";
import { ProjectCard } from "../../../entities/project/ui/ProjectCard";
import { EmptyState } from "@prom/ui/EmptyState";

export function ProjectCardList({
  projects,
  selectedProjectId,
  onSelect,
}: {
  projects: Project[];
  selectedProjectId?: string;
  onSelect?: (projectId: string) => void;
}) {
  if (projects.length === 0) {
    return (
      <EmptyState
        title="Проекты не найдены"
        text="Измените фильтры или попробуйте другой запрос."
      />
    );
  }

  return (
    <div className="project-list">
      {projects.map((project) => (
        <ProjectCard
          key={project.id}
          project={project}
          isSelected={project.id === selectedProjectId}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}
