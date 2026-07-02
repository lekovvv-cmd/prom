import type { Project } from "../../../entities/project/model/types";
import { ProjectCard } from "../../../entities/project/ui/ProjectCard";
import { EmptyState } from "../../../shared/ui/EmptyState";

export function ProjectCardList({ projects }: { projects: Project[] }) {
  if (projects.length === 0) {
    return <EmptyState title="Проекты не найдены" text="Измените фильтры или попробуйте другой запрос." />;
  }

  return (
    <div className="project-grid">
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} />
      ))}
    </div>
  );
}
