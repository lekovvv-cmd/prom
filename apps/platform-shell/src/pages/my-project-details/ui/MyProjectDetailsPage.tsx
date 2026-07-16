import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getMyProject } from "../../../entities/project/api/projectApi";
import type { ProjectDetails as ProjectDetailsType } from "../../../entities/project/model/types";
import { Header } from "../../../widgets/header/ui/Header";
import { ProjectDetails } from "../../../widgets/project-details/ui/ProjectDetails";
import { ProjectTasksPanel } from "../../../widgets/project-tasks/ui/ProjectTasksPanel";
import { Button } from "../../../shared/ui/Button";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";

export function MyProjectDetailsPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState<ProjectDetailsType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadProject = useCallback(async () => {
    if (!projectId) {
      return;
    }
    try {
      setIsLoading(true);
      setError(null);
      const response = await getMyProject(projectId);
      setProject(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить проект");
      setProject(null);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void loadProject();
  }, [loadProject]);

  return (
    <>
      <Header />
      <PageLayout
        title={project?.title ?? "Мой проект"}
        actions={
          <Link to="/my/projects" className="button button-secondary">
            Назад к моим проектам
          </Link>
        }
      >
        {error && <p className="form-error">{error}</p>}
        {isLoading && <Spinner />}
        {!isLoading && project && (
          <div className="my-project-workspace">
            <ProjectDetails project={project} showResponseForm={false} />
            <ProjectTasksPanel project={project} mode="assigned" />
          </div>
        )}
        {!isLoading && !project && !error && (
          <Button variant="secondary" onClick={() => void loadProject()}>
            Повторить
          </Button>
        )}
      </PageLayout>
    </>
  );
}
