import { lazy } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { useAuth } from "@prom/auth";
import { Spinner } from "@prom/ui/Spinner";
import "./platform-foundation.css";
import "./styles.css";
const AdminProjectManagePage = lazy(() =>
  import("./pages/admin-project-manage/ui/AdminProjectManagePage").then(
    (module) => ({ default: module.AdminProjectManagePage }),
  ),
);
const AdminProjectsPage = lazy(() =>
  import("./pages/admin-projects/ui/AdminProjectsPage").then((module) => ({
    default: module.AdminProjectsPage,
  })),
);
const AdminResponsesPage = lazy(() =>
  import("./pages/admin-responses/ui/AdminResponsesPage").then((module) => ({
    default: module.AdminResponsesPage,
  })),
);
const AdminStatsPage = lazy(() =>
  import("./pages/admin-stats/ui/AdminStatsPage").then((module) => ({
    default: module.AdminStatsPage,
  })),
);
const MyProjectDetailsPage = lazy(() =>
  import("./pages/my-project-details/ui/MyProjectDetailsPage").then(
    (module) => ({ default: module.MyProjectDetailsPage }),
  ),
);
const MyProjectsPage = lazy(() =>
  import("./pages/my-projects/ui/MyProjectsPage").then((module) => ({
    default: module.MyProjectsPage,
  })),
);
const MyResponsesPage = lazy(() =>
  import("./pages/my-responses/ui/MyResponsesPage").then((module) => ({
    default: module.MyResponsesPage,
  })),
);
const ProjectDetailsPage = lazy(() =>
  import("./pages/project-details/ui/ProjectDetailsPage").then((module) => ({
    default: module.ProjectDetailsPage,
  })),
);
const ProjectsListPage = lazy(() =>
  import("./pages/projects-list/ui/ProjectsListPage").then((module) => ({
    default: module.ProjectsListPage,
  })),
);
const ProfilePage = lazy(() =>
  import("./pages/profile/ui/ProfilePage").then((module) => ({
    default: module.ProfilePage,
  })),
);

function ProtectedRoute({
  children,
  allowed,
}: {
  children: React.ReactNode;
  allowed?: boolean;
}) {
  const { isLoading, token } = useAuth();
  const location = useLocation();
  if (isLoading) return <Spinner label="Проверяем авторизацию" />;
  if (!token)
    return (
      <Navigate to={loginPath(location.pathname + location.search)} replace />
    );
  return allowed === false ? <Navigate to="/projects" replace /> : children;
}

export default function ProjectsRoutes() {
  const { canManageProjects, isAdmin } = useAuth();
  return (
    <Routes>
      <Route path="/projects" element={<ProjectsListPage />} />
      <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
      <Route
        path="/my/projects"
        element={
          <ProtectedRoute>
            <MyProjectsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/my/projects/:projectId"
        element={
          <ProtectedRoute>
            <MyProjectDetailsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/my/responses"
        element={
          <ProtectedRoute>
            <MyResponsesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={<Navigate to="/admin/projects" replace />}
      />
      <Route
        path="/admin/stats"
        element={
          <ProtectedRoute allowed={isAdmin}>
            <AdminStatsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/projects"
        element={
          <ProtectedRoute allowed={canManageProjects}>
            <AdminProjectsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/projects/:projectId"
        element={
          <ProtectedRoute allowed={canManageProjects}>
            <AdminProjectManagePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/responses"
        element={
          <ProtectedRoute allowed={canManageProjects}>
            <AdminResponsesPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/projects" replace />} />
    </Routes>
  );
}

function loginPath(next: string) {
  const normalized =
    next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/login")
      ? next
      : "/projects";
  return `/login?next=${encodeURIComponent(normalized)}`;
}
