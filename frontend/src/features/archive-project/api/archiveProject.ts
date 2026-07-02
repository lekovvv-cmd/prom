import { archiveAdminProject } from "../../../entities/project/api/projectApi";

export function archiveProject(projectId: string) {
  return archiveAdminProject(projectId);
}
