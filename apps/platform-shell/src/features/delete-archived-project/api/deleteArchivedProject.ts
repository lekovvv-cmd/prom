import { deleteArchivedAdminProject } from "../../../entities/project/api/projectApi";

export function deleteArchivedProject(projectId: string) {
  return deleteArchivedAdminProject(projectId);
}
