import type { ProjectPriority } from "../model/types";
import { Badge } from "../../../shared/ui/Badge";

const labels: Record<ProjectPriority, string> = {
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
  critical: "Критичный"
};

const tones: Record<ProjectPriority, string> = {
  low: "muted",
  medium: "info",
  high: "warning",
  critical: "danger"
};

export function ProjectPriorityBadge({ priority }: { priority: ProjectPriority }) {
  return <Badge tone={tones[priority]}>{labels[priority]}</Badge>;
}
