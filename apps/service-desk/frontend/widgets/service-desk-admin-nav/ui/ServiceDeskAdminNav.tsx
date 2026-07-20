import { NavLink, useLocation } from "react-router-dom";

import { useServiceDeskAccess } from "../../../providers/ServiceDeskAccessProvider";

export const serviceDeskAdminNavItems = [
  ["Обзор", "/admin/service-desk", "service_desk.view_reports"],
  ["Заявки", "/admin/service-desk/tickets", "service_desk.view_all_tickets"],
  ["Каталог", "/admin/service-desk/catalog", "service_desk.manage_catalog"],
  ["Шаблоны", "/admin/service-desk/templates", "service_desk.manage_templates"],
  [
    "Справочники",
    "/admin/service-desk/dictionaries",
    "service_desk.manage_templates",
  ],
  [
    "Согласования",
    "/admin/service-desk/approvals",
    "service_desk.manage_approval_workflows",
  ],
  [
    "Маршрутизация",
    "/admin/service-desk/routing",
    "service_desk.manage_routing",
  ],
  ["SLA", "/admin/service-desk/sla", "service_desk.manage_sla"],
  [
    "Менеджеры и права",
    "/admin/service-desk/access",
    "service_desk.manage_access",
  ],
] as const;

export function ServiceDeskAdminNav() {
  const { user } = useServiceDeskAccess();
  const location = useLocation();
  if (!user) return null;

  return (
    <nav
      className="service-desk-admin-nav"
      aria-label="Администрирование Service Desk"
    >
      {serviceDeskAdminNavItems
        .filter(([, , capability]) => user.capabilities.includes(capability))
        .map(([label, to]) => (
          <NavLink
            key={to}
            to={to}
            className={() => {
              if (to === "/admin/service-desk/sla") {
                return location.pathname === to ? "active" : "";
              }
              if (to === "/admin/service-desk") {
                return location.pathname === to ? "active" : "";
              }
              return location.pathname === to ||
                location.pathname.startsWith(`${to}/`)
                ? "active"
                : "";
            }}
          >
            {label}
          </NavLink>
        ))}
    </nav>
  );
}
