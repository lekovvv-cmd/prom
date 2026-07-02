import { BarChart3, FolderKanban, LogIn, LogOut, MessageSquare, Table2 } from "lucide-react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { Button } from "../../../shared/ui/Button";

export function Header() {
  const { isAdmin, logout, token, user } = useAuth();

  return (
    <header className="app-header">
      <NavLink className="brand" to="/projects">
        <FolderKanban size={24} />
        <span>Витрина проектов ШПИУ</span>
      </NavLink>
      <nav className="main-nav">
        <NavLink to="/projects">Проекты</NavLink>
        {isAdmin && (
          <>
            <NavLink to="/admin/projects">
              <Table2 size={16} />
              Админка
            </NavLink>
            <NavLink to="/admin/responses">
              <MessageSquare size={16} />
              Отклики
            </NavLink>
            <NavLink to="/admin/stats">
              <BarChart3 size={16} />
              Статистика
            </NavLink>
          </>
        )}
      </nav>
      <div className="header-auth">
        {token ? (
          <>
            <span>{user?.email}</span>
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
