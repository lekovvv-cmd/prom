export function splitCompetencies(value: string | null | undefined): string[] {
  if (!value) {
    return [];
  }

  return value
    .split(/[,;\n]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function joinCompetencies(items: string[]): string {
  return Array.from(new Set(items.map((item) => item.trim()).filter(Boolean))).join(", ");
}
