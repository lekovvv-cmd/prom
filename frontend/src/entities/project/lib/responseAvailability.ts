import type { ProjectStatus } from "../model/types";

export function canAcceptProjectResponses(status: ProjectStatus) {
  return status === "active" || status === "paused";
}
