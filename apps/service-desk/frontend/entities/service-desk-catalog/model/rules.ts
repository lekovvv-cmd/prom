export type FormValues = Record<string, unknown>;
export type FormRule = Record<string, unknown>;
export type FormRules = FormRule | FormRule[] | null | undefined;

export function isEmpty(value: unknown) {
  return (
    value === undefined ||
    value === null ||
    value === "" ||
    (Array.isArray(value) && value.length === 0) ||
    (typeof value === "object" &&
      value !== null &&
      !Array.isArray(value) &&
      Object.keys(value).length === 0)
  );
}

export function matchesRules(
  rules: FormRules,
  values: FormValues,
  fallback: boolean,
) {
  if (!rules) return fallback;
  if (Array.isArray(rules))
    return rules.every((rule) => matchesRule(rule, values));
  return matchesRule(rules, values);
}

function matchesRule(rule: FormRule, values: FormValues) {
  const field = typeof rule.field === "string" ? rule.field : "";
  const actual = values[field];
  const expected = rule.value;
  switch (rule.operator ?? "equals") {
    case "equals":
      return actual === expected;
    case "not_equals":
      return actual !== expected;
    case "in":
      return Array.isArray(expected) && expected.includes(actual);
    case "not_in":
      return Array.isArray(expected) && !expected.includes(actual);
    case "is_empty":
      return isEmpty(actual);
    case "is_not_empty":
      return !isEmpty(actual);
    default:
      return false;
  }
}

export function getFieldOptions(field: {
  effective_options?: Array<{ label?: string; value?: string }> | null;
  options?: Array<{ label?: string; value?: string }> | null;
}) {
  return field.effective_options ?? field.options ?? [];
}

export function isFieldVisible(
  field: { visibility_rules?: FormRules },
  values: FormValues,
) {
  return matchesRules(field.visibility_rules, values, true);
}

export function isFieldRequired(
  field: { is_required: boolean; required_rules?: FormRules },
  values: FormValues,
) {
  return field.is_required || matchesRules(field.required_rules, values, false);
}

export function normalizeFieldValue(fieldType: string, value: unknown) {
  if (fieldType === "number" && value !== "") return Number(value);
  if (fieldType === "checkbox") return Boolean(value);
  if (fieldType === "multiselect")
    return Array.isArray(value) ? value.map(String) : [];
  return value;
}

export function fieldControlKind(fieldType: string) {
  if (["textarea", "rich_text"].includes(fieldType)) return "textarea";
  if (["select", "user"].includes(fieldType)) return "select";
  if (fieldType === "multiselect") return "multiselect";
  if (fieldType === "checkbox") return "checkbox";
  if (fieldType === "file") return "file";
  return "input";
}
