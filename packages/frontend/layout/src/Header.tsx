import {
  Archive,
  BarChart3,
  FileText,
  FolderKanban,
  LogIn,
  LogOut,
  MessageSquare,
  Table2,
  UserRound,
} from "lucide-react";
import { createContext, useContext, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { useAuth } from "@prom/auth";
import { Button } from "@prom/ui/Button";
import utmnLogo from "./assets/utmn-logo.png";

const roleLabels = {
  platform_admin: "Администратор платформы",
  project_manager: "Руководитель проектов",
  employee: "Сотрудник",
};

const HeaderToolsContext = createContext<ReactNode>(null);

export function HeaderToolsProvider({
  children,
  tools,
}: {
  children: ReactNode;
  tools: ReactNode;
}) {
  return (
    <HeaderToolsContext.Provider value={tools}>
      {children}
    </HeaderToolsContext.Provider>
  );
}

export function Header() {
  const { canManageProjects, isAdmin, isAuthenticated, logout, modules, user } =
    useAuth();
  const tools = useContext(HeaderToolsContext);
  const location = useLocation();
  const isServiceDeskRoute =
    location.pathname.startsWith("/service-desk") ||
    location.pathname.startsWith("/admin/service-desk");
  const isProjectsRoute = [
    "/projects",
    "/my/projects",
    "/my/responses",
    "/admin/projects",
    "/admin/responses",
    "/admin/stats",
  ].some(
    (prefix) =>
      location.pathname === prefix ||
      location.pathname.startsWith(`${prefix}/`),
  );
  const isModuleRoute = isServiceDeskRoute || isProjectsRoute;
  const moduleAccess = modules ?? [];
  const canAccessProjects =
    !isAuthenticated || moduleAccess.some((module) => module.id === "projects");
  const canAccessServiceDesk =
    !isAuthenticated ||
    moduleAccess.some((module) => module.id === "service-desk");

  return (
    <header className="app-header">
      <NavLink
        className={isModuleRoute ? "brand" : "brand brand-standalone"}
        to={
          isServiceDeskRoute
            ? "/service-desk"
            : isProjectsRoute
              ? "/projects"
              : "/"
        }
      >
        <img className="brand-logo" src={utmnLogo} alt="UTMN" />
        {isModuleRoute ? (
          <span className="brand-copy">
            <strong>
              {isServiceDeskRoute ? "ШПИУ Service Desk" : "ШПИУ Проекты"}
            </strong>
            <small>Тюменский государственный университет</small>
          </span>
        ) : null}
      </NavLink>
      {isModuleRoute ? (
        <nav className="main-nav">
          {isServiceDeskRoute ? (
            <>
              <NavLink end to="/service-desk">
                <Table2 size={15} aria-hidden="true" />
                Каталог
              </NavLink>
              {isAuthenticated ? (
                <NavLink to="/service-desk/my-tickets">
                  <FileText size={15} aria-hidden="true" />
                  Мои заявки
                </NavLink>
              ) : null}
              {isAuthenticated ? (
                <NavLink to="/service-desk/workbench">
                  <Archive size={15} aria-hidden="true" />
                  Рабочее место
                </NavLink>
              ) : null}
            </>
          ) : (
            <>
              <NavLink end to="/projects">
                <FolderKanban size={15} aria-hidden="true" />
                Витрина
              </NavLink>
              {isAuthenticated && user?.role !== "platform_admin" ? (
                <>
                  <NavLink to="/my/projects">
                    <FolderKanban size={15} aria-hidden="true" />
                    Мои проекты
                  </NavLink>
                  <NavLink to="/my/responses">
                    <MessageSquare size={15} aria-hidden="true" />
                    Мои отклики
                  </NavLink>
                </>
              ) : null}
              {canManageProjects && (
                <>
                  <NavLink to="/admin/projects">
                    <Table2 size={15} aria-hidden="true" />
                    Управление
                  </NavLink>
                  <NavLink to="/admin/responses">
                    <MessageSquare size={15} aria-hidden="true" />
                    Отклики
                  </NavLink>
                </>
              )}
              {isAdmin && (
                <NavLink to="/admin/stats">
                  <BarChart3 size={15} aria-hidden="true" />
                  Статистика
                </NavLink>
              )}
            </>
          )}
        </nav>
      ) : null}
      {isModuleRoute ? (
        <div className="header-tools">{isAuthenticated ? tools : null}</div>
      ) : null}
      {isModuleRoute ? (
        <div className="header-auth">
          <div className="header-auth-actions">
            {isAuthenticated ? (
              <>
                <NavLink className="user-chip user-chip-link" to="/profile">
                  <UserRound size={15} />
                  <span>
                    {isServiceDeskRoute
                      ? "Пользователь Service Desk"
                      : user
                        ? roleLabels[user.role]
                        : "Пользователь"}
                  </span>
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
          <nav className="module-switcher" aria-label="Переключатель модулей">
            {canAccessProjects && (
              <NavLink
                to="/projects"
                className={({ isActive }) =>
                  !isServiceDeskRoute && isActive ? "active" : ""
                }
              >
                Проекты
              </NavLink>
            )}
            {canAccessServiceDesk && (
              <NavLink
                to="/service-desk"
                className={() => (isServiceDeskRoute ? "active" : "")}
              >
                Service Desk
              </NavLink>
            )}
          </nav>
        </div>
      ) : null}
    </header>
  );
}
