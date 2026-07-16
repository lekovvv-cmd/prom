import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { useAuth } from "../../platform-shell/src/app/providers/AppProviders";
import { Spinner } from "../../platform-shell/src/shared/ui/Spinner";
import { AdminProjectManagePage } from "../../platform-shell/src/pages/admin-project-manage/ui/AdminProjectManagePage";
import { AdminProjectsPage } from "../../platform-shell/src/pages/admin-projects/ui/AdminProjectsPage";
import { AdminResponsesPage } from "../../platform-shell/src/pages/admin-responses/ui/AdminResponsesPage";
import { AdminStatsPage } from "../../platform-shell/src/pages/admin-stats/ui/AdminStatsPage";
import { MyProjectDetailsPage } from "../../platform-shell/src/pages/my-project-details/ui/MyProjectDetailsPage";
import { MyProjectsPage } from "../../platform-shell/src/pages/my-projects/ui/MyProjectsPage";
import { MyResponsesPage } from "../../platform-shell/src/pages/my-responses/ui/MyResponsesPage";
import { ProjectDetailsPage } from "../../platform-shell/src/pages/project-details/ui/ProjectDetailsPage";
import { ProjectsListPage } from "../../platform-shell/src/pages/projects-list/ui/ProjectsListPage";

function ProtectedRoute({ children, allowed }: { children: React.ReactNode; allowed?: boolean }) {
  const { isLoading, token } = useAuth();
  const location = useLocation();
  if (isLoading) return <Spinner label="Проверяем авторизацию" />;
  if (!token) return <Navigate to={loginPath(location.pathname + location.search)} replace />;
  return allowed === false ? <Navigate to="/projects" replace /> : children;
}

export default function ProjectsRoutes() {
  const { canManageProjects, isAdmin } = useAuth();
  return (
    <Routes>
      <Route path="/projects" element={<ProjectsListPage />} />
      <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
      <Route path="/my/projects" element={<ProtectedRoute><MyProjectsPage /></ProtectedRoute>} />
      <Route path="/my/projects/:projectId" element={<ProtectedRoute><MyProjectDetailsPage /></ProtectedRoute>} />
      <Route path="/my/responses" element={<ProtectedRoute><MyResponsesPage /></ProtectedRoute>} />
      <Route path="/admin" element={<Navigate to="/admin/projects" replace />} />
      <Route path="/admin/stats" element={<ProtectedRoute allowed={isAdmin}><AdminStatsPage /></ProtectedRoute>} />
      <Route path="/admin/projects" element={<ProtectedRoute allowed={canManageProjects}><AdminProjectsPage /></ProtectedRoute>} />
      <Route path="/admin/projects/:projectId" element={<ProtectedRoute allowed={canManageProjects}><AdminProjectManagePage /></ProtectedRoute>} />
      <Route path="/admin/responses" element={<ProtectedRoute allowed={canManageProjects}><AdminResponsesPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/projects" replace />} />
    </Routes>
  );
}

function loginPath(next: string) {
  const normalized = next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/login") ? next : "/projects";
  return `/login?next=${encodeURIComponent(normalized)}`;
}

