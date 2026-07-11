import { useCallback, useEffect, useState } from "react";

import { getServiceDeskContextualCounters } from "../../../entities/service-desk-notification/api/serviceDeskNotificationApi";
import type { ServiceDeskContextualCounters as Counters } from "../../../entities/service-desk-notification/model/types";
import { Badge } from "../../../shared/ui/Badge";
import { onServiceDeskCountersInvalidated } from "../../../shared/lib/serviceDeskCounterInvalidation";

const counterItems: Array<{ key: keyof Counters; label: string }> = [
  { key: "waiting_my_approval", label: "Моё согласование" },
  { key: "assigned_to_me", label: "Назначены мне" },
  { key: "awaiting_my_response", label: "Ждут моего ответа" },
  { key: "sla_breaches", label: "SLA breaches" }
];

export function ContextualCounterList({ counters }: { counters: Counters }) {
  return <div className="service-desk-counters" aria-label="Счётчики Service Desk">
    {counterItems.map(({ key, label }) => counters[key] === null ? null : (
      <span className="service-desk-counter" key={key}>{label}<Badge tone={counters[key] ? "warning" : "neutral"}>{counters[key]}</Badge></span>
    ))}
  </div>;
}

export function ServiceDeskContextualCounters() {
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
  return counters ? <ContextualCounterList counters={counters} /> : null;
}
