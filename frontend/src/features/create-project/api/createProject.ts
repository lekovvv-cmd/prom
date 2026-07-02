import { createAdminProject, uploadAdminProjectAttachment } from "../../../entities/project/api/projectApi";
import type { ProjectMutationPayload } from "../../../entities/project/model/types";

export function createProject(payload: ProjectMutationPayload) {
  return createAdminProject(payload);
}

export async function createProjectWithFiles(payload: ProjectMutationPayload, files: File[]) {
  const project = await createAdminProject(payload);
  await Promise.all(files.map((file) => uploadAdminProjectAttachment(project.id, file)));
  return project;
}
