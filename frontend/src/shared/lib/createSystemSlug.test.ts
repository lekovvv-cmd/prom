import { describe, expect, it } from "vitest";

import { createSystemSlug } from "./createSystemSlug";

describe("createSystemSlug", () => {
  it("creates a Latin snake-case identifier from a Russian label", () => {
    expect(createSystemSlug("Новая дата и время занятия")).toBe("novaya_data_i_vremya_zanyatiya");
  });

  it("normalizes punctuation and keeps existing Latin identifiers", () => {
    expect(createSystemSlug("  Building address / корпус № 1! ")).toBe("building_address_korpus_1");
  });
});
