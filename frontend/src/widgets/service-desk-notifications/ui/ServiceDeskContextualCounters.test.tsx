import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ContextualCounterList } from "./ServiceDeskContextualCounters";

describe("ContextualCounterList", () => {
  it("renders actor counters and hides unavailable SLA counter", () => {
    const html = renderToStaticMarkup(<ContextualCounterList counters={{
      waiting_my_approval: 2, assigned_to_me: 1, awaiting_my_response: 0, sla_breaches: null
    }} />);
    expect(html).toContain("Моё согласование");
    expect(html).toContain("Назначены мне");
    expect(html).not.toContain("Нарушения SLA");
  });

  it("renders SLA breaches when backend authorizes the counter", () => {
    const html = renderToStaticMarkup(<ContextualCounterList counters={{
      waiting_my_approval: 0, assigned_to_me: 0, awaiting_my_response: 0, sla_breaches: 3
    }} />);
    expect(html).toContain("Нарушения SLA");
    expect(html).toContain(">3<");
  });
});
