export const serviceDeskQueryKeys = {
  root: ["service-desk"] as const,
  ticket: (ticketId: string) => ["service-desk", "ticket", ticketId] as const,
  workbench: (filters: Record<string, string | number | boolean | undefined>) => ["service-desk", "workbench", filters] as const
};

