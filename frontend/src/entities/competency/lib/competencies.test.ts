import { describe, expect, it } from "vitest";

import { joinCompetencies, splitCompetencies } from "./competencies";

describe("competency helpers", () => {
  it("splits comma, semicolon and newline separated values", () => {
    expect(splitCompetencies("SQL, Аналитика; UX\nBackend")).toEqual(["SQL", "Аналитика", "UX", "Backend"]);
  });

  it("deduplicates and joins custom competencies", () => {
    expect(joinCompetencies(["SQL", " SQL ", "Интервью"])).toBe("SQL, Интервью");
  });
});
