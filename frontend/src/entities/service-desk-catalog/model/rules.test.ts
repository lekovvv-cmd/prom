import { describe, expect, it } from "vitest";

import { getFieldOptions, matchesRules } from "./rules";

describe("service desk form rules", () => {
  it("requires every rule in an array", () => {
    expect(matchesRules([{ field: "kind", value: "exam" }, { field: "count", operator: "not_equals", value: 0 }], { kind: "exam", count: 2 }, false)).toBe(true);
    expect(matchesRules([{ field: "kind", value: "exam" }, { field: "count", value: 0 }], { kind: "exam", count: 2 }, false)).toBe(false);
  });

  it("prefers resolved dictionary options", () => {
    const options = getFieldOptions({ options: [{ value: "old" }], effective_options: [{ value: "new", label: "Новое" }] });
    expect(options).toEqual([{ value: "new", label: "Новое" }]);
    expect(getFieldOptions({ options: [{ value: "fallback" }] })).toEqual([{ value: "fallback" }]);
  });
});
