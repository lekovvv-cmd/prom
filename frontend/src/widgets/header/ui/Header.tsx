import { BarChart3, FolderKanban, LogIn, LogOut, MessageSquare, Table2, UserRound } from "lucide-react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { useServiceDeskAccess } from "../../../app/providers/ServiceDeskAccessProvider";
import utmnLogo from "../../../shared/assets/utmn-logo.png";
import { Button } from "../../../shared/ui/Button";
import { ServiceDeskNotificationCenter } from "../../service-desk-notifications/ui/ServiceDeskNotificationCenter";
import { ServiceDeskContextualCounters } from "../../service-desk-notifications/ui/ServiceDeskContextualCounters";

const roleLabels = {
  admin: "Админ",
  project_manager: "Руководитель",
  employee: "Сотрудник"
};

export function Header() {
  const { canManageProjects, isAdmin, logout, token, user } = useAuth();
  const { user: serviceDeskUser } = useServiceDeskAccess();
  const canUseWorkbench = serviceDeskUser?.access_type === "service_desk_admin" || ["service_desk.be_assignee", "service_desk.approve", "service_desk.assign", "service_desk.change_priority", "service_desk.view_all_tickets"].some((capability) => serviceDeskUser?.capabilities.includes(capability));

  return (
    <header className="app-header">
      <NavLink className="brand" to="/projects">
        <img className="brand-logo" src={utmnLogo} alt="UTMN" />
        <span className="brand-copy">
          <strong>ШПИУ Проекты</strong>
          <small>Тюменский государственный университет</small>
        </span>
      </NavLink>
      <nav className="main-nav">
        <NavLink to="/projects">
          <FolderKanban size={15} />
          Витрина
        </NavLink>
        {token && serviceDeskUser && <ServiceDeskNotificationCenter />}
        {canUseWorkbench && <NavLink to="/service-desk/workbench"><Table2 size={15} />Workbench</NavLink>}
        {token && user?.role !== "admin" && (
          <>
            <NavLink to="/my/projects">
              <FolderKanban size={15} />
              Мои проекты
            </NavLink>
            <NavLink to="/my/responses">
              <MessageSquare size={15} />
              Мои отклики
            </NavLink>
          </>
        )}
        {canManageProjects && (
          <>
            <NavLink to="/admin/projects">
              <Table2 size={15} />
              Управление
            </NavLink>
            <NavLink to="/admin/responses">
              <MessageSquare size={15} />
              Отклики
            </NavLink>
          </>
        )}
        {isAdmin && (
          <>
            <NavLink to="/admin/stats">
              <BarChart3 size={15} />
              Статистика
            </NavLink>
          </>
        )}
      </nav>
      {serviceDeskUser && <ServiceDeskContextualCounters />}
      <div className="header-auth">
        {token ? (
          <>
            <NavLink className="user-chip user-chip-link" to="/profile">
              <UserRound size={15} />
              <span>{user ? roleLabels[user.role] : "Пользователь"}</span>
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
