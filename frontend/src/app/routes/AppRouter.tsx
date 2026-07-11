import { Link, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "../providers/AppProviders";
import { useServiceDeskAccess } from "../providers/ServiceDeskAccessProvider";
import { AdminProjectManagePage } from "../../pages/admin-project-manage/ui/AdminProjectManagePage";
import { AdminProjectsPage } from "../../pages/admin-projects/ui/AdminProjectsPage";
import { AdminResponsesPage } from "../../pages/admin-responses/ui/AdminResponsesPage";
import { AdminStatsPage } from "../../pages/admin-stats/ui/AdminStatsPage";
import { LoginPage } from "../../pages/login/ui/LoginPage";
import { MyProjectDetailsPage } from "../../pages/my-project-details/ui/MyProjectDetailsPage";
import { MyProjectsPage } from "../../pages/my-projects/ui/MyProjectsPage";
import { MyResponsesPage } from "../../pages/my-responses/ui/MyResponsesPage";
import { ProfilePage } from "../../pages/profile/ui/ProfilePage";
import { ServiceDeskAdminRoutingPage } from "../../pages/service-desk-admin-routing/ui/ServiceDeskAdminRoutingPage";
import { ServiceDeskAdminSlaPage } from "../../pages/service-desk-admin-sla/ui/ServiceDeskAdminSlaPage";
import { ServiceDeskTicketDetailsPage } from "../../pages/service-desk-ticket-details/ui/ServiceDeskTicketDetailsPage";
import { ServiceDeskWorkbenchPage } from "../../pages/service-desk-workbench/ui/ServiceDeskWorkbenchPage";
import { ProjectDetailsPage } from "../../pages/project-details/ui/ProjectDetailsPage";
import { ProjectsListPage } from "../../pages/projects-list/ui/ProjectsListPage";
import { Spinner } from "../../shared/ui/Spinner";
import { Card } from "../../shared/ui/Card";
import { PageLayout } from "../../shared/ui/PageLayout";
import { Header } from "../../widgets/header/ui/Header";

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

function ManagerRoute({ children }: { children: React.ReactNode }) {
  const { canManageProjects, isLoading, token } = useAuth();

  if (isLoading) {
    return <Spinner label="Проверяем авторизацию" />;
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (!canManageProjects) {
    return <Navigate to="/projects" replace />;
  }

  return children;
}

function UserRoute({ children }: { children: React.ReactNode }) {
  const { isLoading, token } = useAuth();

  if (isLoading) {
    return <Spinner label="Проверяем авторизацию" />;
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function ServiceDeskRoute({ children }: { children: React.ReactNode }) {
  const { isLoading: isAuthLoading, token } = useAuth();
  const { error, isLoading, user } = useServiceDeskAccess();

  if (isAuthLoading || isLoading) {
    return <Spinner label="Проверяем доступ к Service Desk" />;
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (!user) {
    return (
      <>
        <Header />
        <PageLayout title="Service Desk">
          <Card>
            <h3>Нет доступа</h3>
            <p className="muted">{error ?? "Профиль Service Desk для пользователя не найден."}</p>
            <Link className="button button-secondary" to="/projects">
              Вернуться к проектам
            </Link>
          </Card>
        </PageLayout>
      </>
    );
  }

  return children;
}

function ServiceDeskRoutingAdminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useServiceDeskAccess();
  const canManageRouting =
    user?.access_type === "service_desk_admin" || user?.capabilities.includes("service_desk.manage_routing");

  if (!canManageRouting) {
    return <Navigate to="/projects" replace />;
  }

  return children;
}

function ServiceDeskSlaAdminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useServiceDeskAccess();
  const allowed = user?.access_type === "service_desk_admin" || user?.capabilities.includes("service_desk.manage_sla");
  return allowed ? children : <Navigate to="/projects" replace />;
}

function ServiceDeskWorkbenchRoute({ children }: { children: React.ReactNode }) {
  const { user } = useServiceDeskAccess();
  const operational = ["service_desk.be_assignee", "service_desk.approve", "service_desk.assign", "service_desk.change_priority", "service_desk.view_all_tickets"];
  const allowed = user?.access_type === "service_desk_admin" || operational.some((capability) => user?.capabilities.includes(capability));
  return allowed ? children : <Navigate to="/projects" replace />;
}

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/projects" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/projects" element={<ProjectsListPage />} />
      <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
      <Route
        path="/service-desk/workbench"
        element={<ServiceDeskRoute><ServiceDeskWorkbenchRoute><ServiceDeskWorkbenchPage /></ServiceDeskWorkbenchRoute></ServiceDeskRoute>}
      />
      <Route
        path="/service-desk/tickets/:ticketId"
        element={
          <ServiceDeskRoute>
            <ServiceDeskTicketDetailsPage />
          </ServiceDeskRoute>
        }
      />
      <Route
        path="/service-desk/admin/routing"
        element={
          <ServiceDeskRoute>
            <ServiceDeskRoutingAdminRoute>
              <ServiceDeskAdminRoutingPage />
            </ServiceDeskRoutingAdminRoute>
          </ServiceDeskRoute>
        }
      />
      <Route path="/service-desk/admin/sla" element={<ServiceDeskRoute><ServiceDeskSlaAdminRoute><ServiceDeskAdminSlaPage /></ServiceDeskSlaAdminRoute></ServiceDeskRoute>} />
      <Route
        path="/profile"
        element={
          <UserRoute>
            <ProfilePage />
          </UserRoute>
        }
      />
      <Route
        path="/my/projects"
        element={
          <UserRoute>
            <MyProjectsPage />
          </UserRoute>
        }
      />
      <Route
        path="/my/projects/:projectId"
        element={
          <UserRoute>
            <MyProjectDetailsPage />
          </UserRoute>
        }
      />
      <Route
        path="/my/responses"
        element={
          <UserRoute>
            <MyResponsesPage />
          </UserRoute>
        }
      />
      <Route path="/admin" element={<Navigate to="/admin/projects" replace />} />
      <Route
        path="/admin/stats"
        element={
          <AdminRoute>
            <AdminStatsPage />
          </AdminRoute>
        }
      />
      <Route
        path="/admin/projects"
        element={
          <ManagerRoute>
            <AdminProjectsPage />
          </ManagerRoute>
        }
      />
      <Route
        path="/admin/projects/:projectId"
        element={
          <ManagerRoute>
            <AdminProjectManagePage />
          </ManagerRoute>
        }
      />
      <Route
        path="/admin/responses"
        element={
          <ManagerRoute>
            <AdminResponsesPage />
          </ManagerRoute>
        }
      />
      <Route path="*" element={<Navigate to="/projects" replace />} />
    </Routes>
  );
}
