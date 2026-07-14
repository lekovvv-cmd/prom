import { describe, expect, it } from "vitest";

import { slaSectionHelp } from "./ServiceDeskAdminSlaPage";

describe("SLA section help", () => {
  it("explains every configuration step in plain language", () => {
    expect(Object.keys(slaSectionHelp)).toEqual(["calendars", "policies", "bindings", "escalations"]);
    expect(slaSectionHelp.bindings).toContain("первое подходящее правило");
  });
});
