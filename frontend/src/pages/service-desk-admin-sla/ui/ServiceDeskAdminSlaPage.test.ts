import { describe, expect, it } from "vitest";

import { SLA_TIMEZONE_OPTIONS, slaSectionHelp } from "./ServiceDeskAdminSlaPage";

describe("SLA section help", () => {
  it("explains every configuration step in plain language", () => {
    expect(Object.keys(slaSectionHelp)).toEqual(["calendars", "policies", "bindings", "escalations"]);
    expect(slaSectionHelp.bindings).toContain("первое подходящее правило");
  });

  it("offers familiar Russian time zones instead of a technical free-text value", () => {
    expect(SLA_TIMEZONE_OPTIONS).toContainEqual({ value: "Asia/Yekaterinburg", label: "Екатеринбург (UTC+5)" });
    expect(SLA_TIMEZONE_OPTIONS).toContainEqual({ value: "Europe/Moscow", label: "Москва (UTC+3)" });
  });
});
