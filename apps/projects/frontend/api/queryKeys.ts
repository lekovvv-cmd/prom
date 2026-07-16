export const projectsQueryKeys = {
  root: ["projects"] as const,
  list: (filters: Record<string, string | number | boolean | undefined>) => ["projects", "list", filters] as const,
  detail: (projectId: string) => ["projects", "detail", projectId] as const
};

