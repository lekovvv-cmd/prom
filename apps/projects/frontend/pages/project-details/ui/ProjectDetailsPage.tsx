import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { getProject } from "../../../entities/project/api/projectApi";
import { projectsQueryKeys } from "../../../api/queryKeys";
import { Header } from "@prom/layout";
import { ProjectDetails } from "../../../widgets/project-details/ui/ProjectDetails";
import { Button } from "@prom/ui/Button";
import { PageLayout } from "@prom/ui/PageLayout";
import { Spinner } from "@prom/ui/Spinner";

export function ProjectDetailsPage() {
  const { projectId } = useParams();
  const projectQuery = useQuery({
    queryKey: projectsQueryKeys.detail(projectId ?? "missing"),
    queryFn: ({ signal }) => getProject(projectId as string, signal),
    enabled: Boolean(projectId),
  });
  const project = projectQuery.data ?? null;
  const error =
    projectQuery.error instanceof Error ? projectQuery.error.message : null;

  return (
    <>
      <Header />
      <PageLayout
        title={project?.title ?? "Проект"}
        actions={
          <Link to="/projects" className="button button-secondary">
            Назад
          </Link>
        }
      >
        {error && <p className="form-error">{error}</p>}
        {projectQuery.isLoading && <Spinner />}
        {!projectQuery.isLoading && project && (
          <ProjectDetails
            project={project}
            onResponseSubmitted={() => void projectQuery.refetch()}
          />
        )}
        {!projectQuery.isLoading && !project && !error && (
          <Button
            variant="secondary"
            onClick={() => void projectQuery.refetch()}
          >
            Повторить
          </Button>
        )}
      </PageLayout>
    </>
  );
}
