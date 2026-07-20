import {
  createAdminProject,
  getAdminProject,
  uploadAdminProjectAttachment,
} from "../../../entities/project/api/projectApi";
import type { ProjectMutationPayload } from "../../../entities/project/model/types";

export async function createProjectWithFiles(
  payload: ProjectMutationPayload,
  files: File[],
) {
  const project = await createAdminProject(payload);
  await Promise.all(
    files.map((file) => uploadAdminProjectAttachment(project.id, file)),
  );
  return getAdminProject(project.id);
}
