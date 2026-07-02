import type { ProjectStatus } from "../model/types";
import { Badge } from "../../../shared/ui/Badge";

const labels: Record<ProjectStatus, string> = {
  draft: "Черновик",
  active: "Активен",
  paused: "Пауза",
  completed: "Завершён",
  archived: "Архив"
};

const tones: Record<ProjectStatus, string> = {
  draft: "neutral",
  active: "success",
  paused: "warning",
  completed: "info",
  archived: "muted"
};

export function ProjectStatusBadge({ status }: { status: ProjectStatus }) {
  return <Badge tone={tones[status]}>{labels[status]}</Badge>;
}
