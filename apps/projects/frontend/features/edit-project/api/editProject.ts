import {
  getAdminProject,
  updateAdminProject,
  uploadAdminProjectAttachment,
} from "../../../entities/project/api/projectApi";
import type { ProjectMutationPayload } from "../../../entities/project/model/types";

export async function editProjectWithFiles(
  projectId: string,
  payload: Partial<ProjectMutationPayload>,
  files: File[],
) {
  const project = await updateAdminProject(projectId, payload);
  await Promise.all(
    files.map((file) => uploadAdminProjectAttachment(projectId, file)),
  );
  return getAdminProject(project.id);
}
