import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getServiceDeskContextualCounters } from "../../../entities/service-desk-notification/api/serviceDeskNotificationApi";
import type { ServiceDeskContextualCounters as Counters } from "../../../entities/service-desk-notification/model/types";
import type { WorkbenchQuickView } from "../../../entities/service-desk-workbench/model/types";
import { Badge } from "../../../shared/ui/Badge";
import { onServiceDeskCountersInvalidated } from "../../../shared/lib/serviceDeskCounterInvalidation";

const counterItems: Array<{ key: keyof Counters; label: string; quickView: WorkbenchQuickView }> = [
  { key: "waiting_my_approval", label: "Моё согласование", quickView: "waiting_approval" },
  { key: "assigned_to_me", label: "Назначены мне", quickView: "assigned_to_me" },
  { key: "awaiting_my_response", label: "Ждут моего ответа", quickView: "waiting_requester" },
  { key: "sla_breaches", label: "Нарушения SLA", quickView: "sla_breached" }
];

export function ContextualCounterList({ counters, interactive = false }: { counters: Counters; interactive?: boolean }) {
  return <div className="service-desk-counters" aria-label="Счётчики Service Desk">
    {counterItems.map(({ key, label, quickView }) => {
      if (counters[key] === null) return null;
      const content = <>{label}<Badge tone={counters[key] ? "warning" : "neutral"}>{counters[key]}</Badge></>;
      return interactive
        ? <Link className="service-desk-counter" key={key} to={`/service-desk/workbench?quick_view=${quickView}`} aria-label={`Открыть «${label}» в рабочем месте`}>{content}</Link>
        : <span className="service-desk-counter" key={key}>{content}</span>;
    })}
  </div>;
}

export function ServiceDeskContextualCounters({ interactive = false }: { interactive?: boolean }) {
  const [counters, setCounters] = useState<Counters | null>(null);
  const refresh = useCallback(() => {
    void getServiceDeskContextualCounters().then(setCounters).catch(() => setCounters(null));
  }, []);
  useEffect(() => {
    refresh();
    const unsubscribe = onServiceDeskCountersInvalidated(refresh);
    const timer = window.setInterval(refresh, 60_000);
    return () => { unsubscribe(); window.clearInterval(timer); };
  }, [refresh]);
  return counters ? <ContextualCounterList counters={counters} interactive={interactive} /> : null;
}
