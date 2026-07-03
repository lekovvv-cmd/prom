export function splitProjectTasks(value: string | null | undefined): string[] {
  if (!value) {
    return [];
  }

  return value
    .split(/\r?\n|[;\u2022]/)
    .map((item) => item.replace(/^[-\u2013\u2014*]\s*/, "").trim())
    .filter(Boolean);
}
