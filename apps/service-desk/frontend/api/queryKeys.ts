export const serviceDeskQueryKeys = {
  root: ["service-desk"] as const,
  access: (token: string | null) => ["service-desk", "access", token] as const,
  catalog: () => ["service-desk", "catalog"] as const,
  myTickets: () => ["service-desk", "my-tickets"] as const,
  ticket: (ticketId: string) => ["service-desk", "ticket", ticketId] as const,
  workbench: (filters: Record<string, string | number | boolean | undefined>) =>
    ["service-desk", "workbench", filters] as const,
};
