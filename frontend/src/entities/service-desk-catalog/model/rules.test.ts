import { describe, expect, it } from "vitest";

import { fieldControlKind, getFieldOptions, isFieldRequired, isFieldVisible, matchesRules, normalizeFieldValue } from "./rules";

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

  it("supports empty and non-empty dynamic conditions", () => {
    expect(matchesRules({ field: "details", operator: "is_empty" }, { details: "" }, false)).toBe(true);
    expect(matchesRules({ field: "details", operator: "is_not_empty" }, { details: "Описание" }, false)).toBe(true);
  });

  it("computes conditional visibility and required state", () => {
    const values = { kind: "exam" };
    expect(isFieldVisible({ visibility_rules: { field: "kind", value: "exam" } }, values)).toBe(true);
    expect(isFieldVisible({ visibility_rules: { field: "kind", value: "other" } }, values)).toBe(false);
    expect(isFieldRequired({ is_required: false, required_rules: { field: "kind", value: "exam" } }, values)).toBe(true);
  });

  it("normalizes renderer values and maps controls", () => {
    expect(normalizeFieldValue("number", "12")).toBe(12);
    expect(normalizeFieldValue("checkbox", 1)).toBe(true);
    expect(normalizeFieldValue("multiselect", [1, "two"])).toEqual(["1", "two"]);
    expect(fieldControlKind("rich_text")).toBe("textarea");
    expect(fieldControlKind("user")).toBe("select");
    expect(fieldControlKind("file")).toBe("file");
  });
});
