import { restoreArchivedAdminProject } from "../../../entities/project/api/projectApi";

export function restoreArchivedProject(projectId: string) {
  return restoreArchivedAdminProject(projectId);
}
