import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "../providers/AppProviders";
import { AdminProjectsPage } from "../../pages/admin-projects/ui/AdminProjectsPage";
import { AdminResponsesPage } from "../../pages/admin-responses/ui/AdminResponsesPage";
import { AdminStatsPage } from "../../pages/admin-stats/ui/AdminStatsPage";
import { LoginPage } from "../../pages/login/ui/LoginPage";
import { ProjectDetailsPage } from "../../pages/project-details/ui/ProjectDetailsPage";
import { ProjectsListPage } from "../../pages/projects-list/ui/ProjectsListPage";
import { Spinner } from "../../shared/ui/Spinner";

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAdmin, isLoading, token } = useAuth();

  if (isLoading) {
    return <Spinner label="Проверяем авторизацию" />;
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin) {
    return <Navigate to="/projects" replace />;
  }

  return children;
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/projects" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/projects" element={<ProjectsListPage />} />
      <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
      <Route path="/admin" element={<Navigate to="/admin/projects" replace />} />
      <Route
        path="/admin/projects"
        element={
          <AdminRoute>
            <AdminProjectsPage />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/responses"
        element={
          <AdminRoute>
            <AdminResponsesPage />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/stats"
        element={
          <AdminRoute>
            <AdminStatsPage />
          </AdminRoute>
        }
      />
      <Route path="*" element={<Navigate to="/projects" replace />} />
    </Routes>
  );
}
