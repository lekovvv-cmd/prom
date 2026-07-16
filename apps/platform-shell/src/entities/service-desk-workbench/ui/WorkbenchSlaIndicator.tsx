import type { WorkbenchTicket } from "../model/types";
import { formatDateTime } from "../../../shared/lib/date";
import { Badge } from "../../../shared/ui/Badge";

const stateMeta = {
  no_sla: { label: "Без SLA", tone: "muted" },
  on_track: { label: "SLA в норме", tone: "success" },
  paused: { label: "SLA на паузе", tone: "neutral" },
  warning: { label: "Риск SLA", tone: "warning" },
  breached: { label: "SLA нарушен", tone: "danger" }
} as const;

const metricLabels = { first_response: "Первый ответ", resolution: "Решение" } as const;

export function WorkbenchSlaIndicator({ sla }: { sla: WorkbenchTicket["sla"] }) {
  const state = stateMeta[sla.state];
  return <div className="workbench-sla"><Badge tone={state.tone}>{state.label}</Badge>
    {sla.metric && <small>{metricLabels[sla.metric]}{sla.due_at ? ` · до ${formatDateTime(sla.due_at)}` : ""}</small>}
  </div>;
}
