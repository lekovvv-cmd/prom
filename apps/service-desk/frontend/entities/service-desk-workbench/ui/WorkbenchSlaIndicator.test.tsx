import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { WorkbenchSlaIndicator } from "./WorkbenchSlaIndicator";

describe("WorkbenchSlaIndicator", () => {
  it.each([
    ["no_sla", "Без SLA"],
    ["paused", "SLA на паузе"],
    ["warning", "Риск SLA"],
    ["breached", "SLA нарушен"],
  ] as const)("renders %s with text", (state, label) => {
    expect(
      renderToStaticMarkup(
        <WorkbenchSlaIndicator sla={{ state, metric: null, due_at: null }} />,
      ),
    ).toContain(label);
  });
  it("renders active metric and server due date", () => {
    const html = renderToStaticMarkup(
      <WorkbenchSlaIndicator
        sla={{
          state: "on_track",
          metric: "first_response",
          due_at: "2026-01-01T12:30:00Z",
        }}
      />,
    );
    expect(html).toContain("Первый ответ");
    expect(html).toContain("SLA в норме");
  });
});
