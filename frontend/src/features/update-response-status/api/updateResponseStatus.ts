import { updateAdminResponseStatus } from "../../../entities/project-response/api/projectResponseApi";
import type { ProjectResponseStatus } from "../../../entities/project-response/model/types";

export function updateResponseStatus(responseId: string, status: ProjectResponseStatus) {
  return updateAdminResponseStatus(responseId, status);
}
