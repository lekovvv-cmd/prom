import type { ProjectResponseStatus } from "../model/types";
import { Badge, type BadgeTone } from "@prom/ui/Badge";

export const responseStatusLabels: Record<ProjectResponseStatus, string> = {
  new: "Новый",
  viewed: "Просмотрен",
  contacted: "Связались",
  accepted: "Принят",
  rejected: "Отклонён",
  cancelled: "Отозван",
};

const tones: Record<ProjectResponseStatus, BadgeTone> = {
  new: "warning",
  viewed: "info",
  contacted: "info",
  accepted: "success",
  rejected: "danger",
  cancelled: "muted",
};

export function ResponseStatusBadge({
  status,
}: {
  status: ProjectResponseStatus;
}) {
  return <Badge tone={tones[status]}>{responseStatusLabels[status]}</Badge>;
}
