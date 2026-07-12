export type ServiceDeskAdminLandingUser = {
  access_type: "service_desk_manager" | "service_desk_admin";
  capabilities: string[];
};

const landingOptions = [
  ["service_desk.view_reports", "/admin/service-desk"],
  ["service_desk.view_all_tickets", "/admin/service-desk/tickets"],
  ["service_desk.manage_catalog", "/admin/service-desk/catalog"],
  ["service_desk.manage_templates", "/admin/service-desk/templates"],
  ["service_desk.manage_approval_workflows", "/admin/service-desk/approvals"],
  ["service_desk.manage_routing", "/admin/service-desk/routing"],
  ["service_desk.manage_sla", "/admin/service-desk/sla"],
  ["service_desk.manage_access", "/admin/service-desk/access"],
] as const;

export function getServiceDeskAdminLanding(user: ServiceDeskAdminLandingUser | null | undefined) {
  if (!user) return null;
  if (user.access_type === "service_desk_admin") return "/admin/service-desk";
  return landingOptions.find(([capability]) => (user.capabilities ?? []).includes(capability))?.[1] ?? null;
}
