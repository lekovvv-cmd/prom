import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { canAcceptProjectResponses } from "../../../entities/project/lib/responseAvailability";
import type { ProjectDetails as ProjectDetailsType } from "../../../entities/project/model/types";
import { getProject } from "../../../entities/project/api/projectApi";
import { Header } from "../../../widgets/header/ui/Header";
import { ProjectDetails } from "../../../widgets/project-details/ui/ProjectDetails";
import { Button } from "../../../shared/ui/Button";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";

export function ProjectDetailsPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState<ProjectDetailsType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadProject = useCallback(async (showSpinner = true) => {
    if (!projectId) {
      return;
    }
    try {
      if (showSpinner) {
        setIsLoading(true);
      }
      setError(null);
      const response = await getProject(projectId);
      setProject(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось загрузить проект");
    } finally {
      if (showSpinner) {
        setIsLoading(false);
      }
    }
  }, [projectId]);

  useEffect(() => {
    void loadProject(true);
  }, [loadProject]);

  const subtitle =
    project && !canAcceptProjectResponses(project.status)
      ? "Детали проекта. Новые отклики на этот статус закрыты"
      : "Детали проекта и форма отклика";

  return (
    <>
      <Header />
      <PageLayout
        title={project?.title ?? "Проект"}
        subtitle={subtitle}
        actions={
          <Link to="/projects" className="button button-secondary">
            Назад
          </Link>
        }
      >
        {error && <p className="form-error">{error}</p>}
        {isLoading && <Spinner />}
        {!isLoading && project && (
          <ProjectDetails project={project} onResponseSubmitted={() => void loadProject(false)} />
        )}
        {!isLoading && !project && !error && (
          <Button variant="secondary" onClick={() => void loadProject(true)}>
            Повторить
          </Button>
        )}
      </PageLayout>
    </>
  );
}
