import { deleteAdminResponse } from "../../../entities/project-response/api/projectResponseApi";

export function deleteProjectResponse(responseId: string) {
  return deleteAdminResponse(responseId);
}
