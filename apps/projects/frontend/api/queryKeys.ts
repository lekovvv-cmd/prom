export const projectsQueryKeys = {
  root: ["projects"] as const,
  list: (filters: Record<string, string | number | boolean | undefined>) =>
    ["projects", "list", filters] as const,
  showcase: (
    filters: Record<string, string | number | boolean | undefined>,
    recommendations: boolean,
  ) => ["projects", "showcase", filters, { recommendations }] as const,
  myList: (filters: Record<string, string | number | boolean | undefined>) =>
    ["projects", "my-list", filters] as const,
  detail: (projectId: string) => ["projects", "detail", projectId] as const,
};
