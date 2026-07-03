import { withdrawMyResponse } from "../../../entities/project-response/api/projectResponseApi";

export function withdrawProjectResponse(responseId: string) {
  return withdrawMyResponse(responseId);
}
