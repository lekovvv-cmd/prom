import { BarChart3, FolderKanban, LogIn, LogOut, MessageSquare, Table2, UserRound } from "lucide-react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import utmnLogo from "../../../shared/assets/utmn-logo.png";
import { Button } from "../../../shared/ui/Button";

const roleLabels = {
  admin: "Админ",
  project_manager: "Руководитель",
  employee: "Сотрудник"
};

export function Header() {
  const { canManageProjects, isAdmin, logout, token, user } = useAuth();

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
