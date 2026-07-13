import { Archive, BarChart3, FileText, FolderKanban, LogIn, LogOut, MessageSquare, Table2, UserRound } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { useServiceDeskAccess } from "../../../app/providers/ServiceDeskAccessProvider";
import { getServiceDeskAdminLanding } from "../../../entities/service-desk-admin/model/adminLanding";
import utmnLogo from "../../../shared/assets/utmn-logo.png";
import { Button } from "../../../shared/ui/Button";
import { ServiceDeskContextualCounters } from "../../service-desk-notifications/ui/ServiceDeskContextualCounters";
import { ServiceDeskNotificationCenter } from "../../service-desk-notifications/ui/ServiceDeskNotificationCenter";

const roleLabels = {
  platform_admin: "Администратор платформы",
  project_manager: "Руководитель проектов",
  employee: "Сотрудник"
};

export function Header() {
  const { canManageProjects, isAdmin, logout, token, user } = useAuth();
  const { user: serviceDeskUser } = useServiceDeskAccess();
  const location = useLocation();
  const isServiceDeskRoute = location.pathname.startsWith("/service-desk") || location.pathname.startsWith("/admin/service-desk");
  const canUseWorkbench = serviceDeskUser?.access_type === "service_desk_admin" || ["service_desk.be_assignee", "service_desk.approve", "service_desk.assign", "service_desk.change_priority", "service_desk.view_all_tickets"].some((capability) => serviceDeskUser?.capabilities?.includes(capability));
  const adminLanding = getServiceDeskAdminLanding(serviceDeskUser);

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
            <NavLink end to="/service-desk"><Table2 size={15} aria-hidden="true" />Каталог</NavLink>
            {token && <NavLink to="/service-desk/my-tickets"><FileText size={15} aria-hidden="true" />Мои заявки</NavLink>}
            {canUseWorkbench && <NavLink to="/service-desk/workbench"><Archive size={15} aria-hidden="true" />Рабочее место</NavLink>}
            {adminLanding ? <NavLink to={adminLanding}><BarChart3 size={15} aria-hidden="true" />Администрирование</NavLink> : null}
          </>
        ) : (
          <>
            <NavLink end to="/projects"><FolderKanban size={15} aria-hidden="true" />Витрина</NavLink>
            {token && user?.role !== "platform_admin" && (
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
      <div className="header-tools">
        {token && serviceDeskUser && <ServiceDeskNotificationCenter />}
        <nav className="module-switcher" aria-label="Переключатель модулей">
          <NavLink to="/projects" className={({ isActive }) => !isServiceDeskRoute && isActive ? "active" : ""}>Проекты</NavLink>
          {!token || serviceDeskUser ? (
            <NavLink to="/service-desk" className={() => isServiceDeskRoute ? "active" : ""}>Service Desk</NavLink>
          ) : null}
        </nav>
      </div>
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
      {isServiceDeskRoute && token && serviceDeskUser ? <div className="service-desk-header-status"><ServiceDeskContextualCounters /></div> : null}
    </header>
  );
}
