import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
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

  it("links each available counter to its matching workbench view", () => {
    const html = renderToStaticMarkup(<MemoryRouter><ContextualCounterList interactive counters={{
      waiting_my_approval: 2, assigned_to_me: 1, awaiting_my_response: 3, sla_breaches: 4
    }} /></MemoryRouter>);

    expect(html).toContain("/service-desk/workbench?quick_view=waiting_approval");
    expect(html).toContain("/service-desk/workbench?quick_view=assigned_to_me");
    expect(html).toContain("/service-desk/workbench?quick_view=waiting_requester");
    expect(html).toContain("/service-desk/workbench?quick_view=sla_breached");
  });
});
