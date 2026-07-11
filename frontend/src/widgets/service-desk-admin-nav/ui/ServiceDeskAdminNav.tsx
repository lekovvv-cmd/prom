import { NavLink, useLocation } from "react-router-dom";
import { useServiceDeskAccess } from "../../../app/providers/ServiceDeskAccessProvider";

const items = [
  ["Обзор", "/admin/service-desk", "service_desk.view_reports"],
  ["Заявки", "/admin/service-desk/tickets", "service_desk.view_all_tickets"],
  ["Каталог", "/admin/service-desk/catalog", "service_desk.manage_catalog"],
  ["Шаблоны", "/admin/service-desk/templates", "service_desk.manage_templates"],
  ["Согласования", "/admin/service-desk/approvals", "service_desk.manage_approval_workflows"],
  ["Маршрутизация", "/admin/service-desk/routing", "service_desk.manage_routing"],
  ["SLA", "/admin/service-desk/sla", "service_desk.manage_sla"],
  ["Рабочие календари", "/admin/service-desk/calendars", "service_desk.manage_sla"],
  ["Менеджеры и права", "/admin/service-desk/access", "service_desk.manage_access"],
  ["Уведомления / доставка", "/admin/service-desk/notifications", "service_desk.manage_access"]
] as const;

export function ServiceDeskAdminNav() {
  const { user } = useServiceDeskAccess(); const location = useLocation();
  if (!user) return null;
  return <nav className="service-desk-admin-nav" aria-label="Администрирование Service Desk">{items.filter(([, , capability]) => user.capabilities.includes(capability)).map(([label,to]) => <NavLink key={to} to={to} className={() => location.pathname === to || location.pathname.startsWith(`${to}/`) ? "active" : ""}>{label}</NavLink>)}</nav>;
}
