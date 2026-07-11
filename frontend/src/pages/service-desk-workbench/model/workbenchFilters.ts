export type WorkbenchFilters = Record<string, string>;

export const initialWorkbenchFilters: WorkbenchFilters = { page: "1", page_size: "25" };

export function updateWorkbenchFilter(
  current: WorkbenchFilters,
  key: string,
  value: string
): WorkbenchFilters {
  return {
    ...current,
    [key]: value,
    ...(key === "category_id" ? { service_id: "" } : {}),
    page: "1"
  };
}

export function updateWorkbenchPage(
  current: WorkbenchFilters,
  nextPage: number,
  totalPages: number
): WorkbenchFilters {
  const page = Math.max(1, Math.min(nextPage, Math.max(1, totalPages)));
  return { ...current, page: String(page) };
}

export function buildWorkbenchParams(filters: WorkbenchFilters, search: string) {
  const value = new URLSearchParams();
  Object.entries(filters).forEach(([key, item]) => {
    if (item) value.set(key, item);
  });
  if (search.trim()) value.set("q", search.trim());
  return value;
}

export function shouldShowInitialWorkbenchSpinner(loading: boolean, hasData: boolean) {
  return loading && !hasData;
}
