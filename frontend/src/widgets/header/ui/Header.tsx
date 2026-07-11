import { Archive, BarChart3, FileText, FolderKanban, LogIn, LogOut, MessageSquare, Table2, UserRound } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { useServiceDeskAccess } from "../../../app/providers/ServiceDeskAccessProvider";
import utmnLogo from "../../../shared/assets/utmn-logo.png";
import { Button } from "../../../shared/ui/Button";
import { ServiceDeskNotificationCenter } from "../../service-desk-notifications/ui/ServiceDeskNotificationCenter";

const roleLabels = {
  admin: "Админ",
  project_manager: "Руководитель",
  employee: "Сотрудник"
};

export function Header() {
  const { canManageProjects, isAdmin, logout, token, user } = useAuth();
  const { user: serviceDeskUser } = useServiceDeskAccess();
  const location = useLocation();
  const isServiceDeskRoute = location.pathname.startsWith("/service-desk") || location.pathname.startsWith("/admin/service-desk");
  const canUseWorkbench = serviceDeskUser?.access_type === "service_desk_admin" || ["service_desk.be_assignee", "service_desk.approve", "service_desk.assign", "service_desk.change_priority", "service_desk.view_all_tickets"].some((capability) => serviceDeskUser?.capabilities?.includes(capability));
  const canViewReports = serviceDeskUser?.access_type === "service_desk_admin" || serviceDeskUser?.capabilities?.includes("service_desk.view_reports");
  const canManageAccess = serviceDeskUser?.access_type === "service_desk_admin" || serviceDeskUser?.capabilities?.includes("service_desk.manage_access");

  return (
    <header className="app-header">
      <NavLink className="brand" to={isServiceDeskRoute ? "/service-desk" : "/projects"}>
        <img className="brand-logo" src={utmnLogo} alt="UTMN" />
        <span className="brand-copy">
          <strong>{isServiceDeskRoute ? "ШПИУ Service Desk" : "ШПИУ Проекты"}</strong>
          <small>Тюменский государственный университет</small>
        </span>
      </NavLink>
      <nav className="main-nav">
        {isServiceDeskRoute ? (
          <>
            <NavLink to="/service-desk"><Table2 size={15} aria-hidden="true" />Каталог</NavLink>
            {token && <NavLink to="/service-desk/my-tickets"><FileText size={15} aria-hidden="true" />Мои заявки</NavLink>}
            {canUseWorkbench && <NavLink to="/service-desk/workbench"><Archive size={15} aria-hidden="true" />Рабочее место</NavLink>}
            {canViewReports || canManageAccess ? <NavLink to="/admin/service-desk"><BarChart3 size={15} aria-hidden="true" />Администрирование</NavLink> : null}
            {token && serviceDeskUser && <ServiceDeskNotificationCenter />}
          </>
        ) : (
          <>
            <NavLink to="/projects"><FolderKanban size={15} aria-hidden="true" />Витрина</NavLink>
            {token && serviceDeskUser && <ServiceDeskNotificationCenter />}
            {token && user?.role !== "admin" && (
              <>
                <NavLink to="/my/projects"><FolderKanban size={15} aria-hidden="true" />Мои проекты</NavLink>
                <NavLink to="/my/responses"><MessageSquare size={15} aria-hidden="true" />Мои отклики</NavLink>
              </>
            )}
            {canManageProjects && (
              <>
                <NavLink to="/admin/projects"><Table2 size={15} aria-hidden="true" />Управление</NavLink>
                <NavLink to="/admin/responses"><MessageSquare size={15} aria-hidden="true" />Отклики</NavLink>
              </>
            )}
            {isAdmin && <NavLink to="/admin/stats"><BarChart3 size={15} aria-hidden="true" />Статистика</NavLink>}
          </>
        )}
      </nav>
      <nav className="module-switcher" aria-label="Переключатель модулей">
        <NavLink to="/projects" className={({ isActive }) => !isServiceDeskRoute && isActive ? "active" : ""}>Проекты</NavLink>
        <NavLink to="/service-desk" className={() => isServiceDeskRoute ? "active" : ""}>Service Desk</NavLink>
      </nav>
      <div className="header-auth">
        {token ? (
          <>
            <NavLink className="user-chip user-chip-link" to="/profile">
              <UserRound size={15} />
              <span>{isServiceDeskRoute ? (serviceDeskUser?.access_type === "service_desk_admin" ? "Администратор Service Desk" : serviceDeskUser ? "Менеджер Service Desk" : "Пользователь Service Desk") : user ? roleLabels[user.role] : "Пользователь"}</span>
              <small>{user?.email}</small>
            </NavLink>
            <Button variant="ghost" onClick={logout}>
              <LogOut size={16} />
              Выйти
            </Button>
          </>
        ) : (
          <NavLink className="button button-secondary" to="/login">
            <LogIn size={16} />
            Войти
          </NavLink>
        )}
      </div>
    </header>
  );
}
