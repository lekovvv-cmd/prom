import { useEffect, useState } from "react";

import { getServiceDeskContextualCounters } from "../../../entities/service-desk-notification/api/serviceDeskNotificationApi";
import type { ServiceDeskContextualCounters as Counters } from "../../../entities/service-desk-notification/model/types";
import { Badge } from "../../../shared/ui/Badge";

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
  useEffect(() => {
    let current = true;
    void getServiceDeskContextualCounters().then((value) => { if (current) setCounters(value); }).catch(() => { if (current) setCounters(null); });
    return () => { current = false; };
  }, []);
  return counters ? <ContextualCounterList counters={counters} /> : null;
}
