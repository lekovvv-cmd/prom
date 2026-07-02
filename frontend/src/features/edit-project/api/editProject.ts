import { updateAdminProject } from "../../../entities/project/api/projectApi";
import type { ProjectMutationPayload } from "../../../entities/project/model/types";

export function editProject(projectId: string, payload: Partial<ProjectMutationPayload>) {
  return updateAdminProject(projectId, payload);
}
