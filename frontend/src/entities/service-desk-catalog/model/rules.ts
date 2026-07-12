export type FormValues = Record<string, unknown>;
export type FormRule = Record<string, unknown>;
export type FormRules = FormRule | FormRule[] | null | undefined;

export function isEmpty(value: unknown) {
  return value === undefined || value === null || value === "" || (Array.isArray(value) && value.length === 0) || (typeof value === "object" && value !== null && !Array.isArray(value) && Object.keys(value).length === 0);
}

export function matchesRules(rules: FormRules, values: FormValues, fallback: boolean) {
  if (!rules) return fallback;
  if (Array.isArray(rules)) return rules.every((rule) => matchesRule(rule, values));
  return matchesRule(rules, values);
}

function matchesRule(rule: FormRule, values: FormValues) {
  const field = typeof rule.field === "string" ? rule.field : "";
  const actual = values[field];
  const expected = rule.value;
  switch (rule.operator ?? "equals") {
    case "equals": return actual === expected;
    case "not_equals": return actual !== expected;
    case "in": return Array.isArray(expected) && expected.includes(actual);
    case "not_in": return Array.isArray(expected) && !expected.includes(actual);
    case "is_empty": return isEmpty(actual);
    case "is_not_empty": return !isEmpty(actual);
    default: return false;
  }
}

export function getFieldOptions(field: { effective_options?: Array<{ label?: string; value?: string }> | null; options?: Array<{ label?: string; value?: string }> | null }) {
  return field.effective_options ?? field.options ?? [];
}
