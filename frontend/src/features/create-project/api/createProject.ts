import { createAdminProject } from "../../../entities/project/api/projectApi";
import type { ProjectMutationPayload } from "../../../entities/project/model/types";

export function createProject(payload: ProjectMutationPayload) {
  return createAdminProject(payload);
}
