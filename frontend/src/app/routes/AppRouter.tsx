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
import { ServiceDeskAdminDashboardPage } from "../../pages/service-desk-admin-dashboard/ui/ServiceDeskAdminDashboardPage";
import { ServiceDeskAdminAccessPage } from "../../pages/service-desk-admin-access/ui/ServiceDeskAdminAccessPage";
import { ServiceDeskCatalogPage } from "../../pages/service-desk-catalog/ui/ServiceDeskCatalogPage";
import { ServiceDeskMyTicketsPage } from "../../pages/service-desk-my-tickets/ui/ServiceDeskMyTicketsPage";
import { ServiceDeskServiceFormPage } from "../../pages/service-desk-service-form/ui/ServiceDeskServiceFormPage";
import { ProjectDetailsPage } from "../../pages/project-details/ui/ProjectDetailsPage";
import { ProjectsListPage } from "../../pages/projects-list/ui/ProjectsListPage";
import { Spinner } from "../../shared/ui/Spinner";
import { Card } from "../../shared/ui/Card";
import { PageLayout } from "../../shared/ui/PageLayout";
import { Header } from "../../widgets/header/ui/Header";
import { ServiceDeskAdminLayout } from "../../widgets/service-desk-admin-layout/ui/ServiceDeskAdminLayout";
import { ServiceDeskContextualCounters } from "../../widgets/service-desk-notifications/ui/ServiceDeskContextualCounters";

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

  return <><ServiceDeskContextualCounters />{children}</>;
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

function ServiceDeskReportsRoute({ children }: { children: React.ReactNode }) {
  const { user } = useServiceDeskAccess();
  return user?.capabilities.includes("service_desk.view_reports") ? children : <Navigate to="/projects" replace />;
}
function ServiceDeskAccessAdminRoute({ children }: { children: React.ReactNode }) { const { user } = useServiceDeskAccess(); return user?.capabilities.includes("service_desk.manage_access") ? children : <Navigate to="/projects" replace />; }

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/projects" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/projects" element={<ProjectsListPage />} />
      <Route path="/projects/:projectId" element={<ProjectDetailsPage />} />
      <Route path="/service-desk" element={<ServiceDeskCatalogPage />} />
      <Route path="/service-desk/catalog" element={<ServiceDeskCatalogPage />} />
      <Route path="/service-desk/services/:serviceId" element={<ServiceDeskServiceFormPage />} />
      <Route
        path="/admin/service-desk"
        element={<ServiceDeskRoute><ServiceDeskReportsRoute><ServiceDeskAdminLayout><ServiceDeskAdminDashboardPage /></ServiceDeskAdminLayout></ServiceDeskReportsRoute></ServiceDeskRoute>}
      />
      <Route path="/admin/service-desk/access" element={<ServiceDeskRoute><ServiceDeskAccessAdminRoute><ServiceDeskAdminLayout><ServiceDeskAdminAccessPage /></ServiceDeskAdminLayout></ServiceDeskAccessAdminRoute></ServiceDeskRoute>} />
      <Route
        path="/service-desk/workbench"
        element={<ServiceDeskRoute><ServiceDeskWorkbenchRoute><Header /><ServiceDeskWorkbenchPage /></ServiceDeskWorkbenchRoute></ServiceDeskRoute>}
      />
      <Route
        path="/service-desk/my-tickets"
        element={<ServiceDeskRoute><ServiceDeskMyTicketsPage /></ServiceDeskRoute>}
      />
      <Route
        path="/service-desk/tickets"
        element={<ServiceDeskRoute><ServiceDeskMyTicketsPage /></ServiceDeskRoute>}
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
        path="/admin/service-desk/routing"
        element={
          <ServiceDeskRoute>
            <ServiceDeskRoutingAdminRoute>
              <ServiceDeskAdminLayout><ServiceDeskAdminRoutingPage /></ServiceDeskAdminLayout>
            </ServiceDeskRoutingAdminRoute>
          </ServiceDeskRoute>
        }
      />
      <Route path="/admin/service-desk/tickets" element={<ServiceDeskRoute><ServiceDeskWorkbenchRoute><ServiceDeskAdminLayout><ServiceDeskWorkbenchPage /></ServiceDeskAdminLayout></ServiceDeskWorkbenchRoute></ServiceDeskRoute>} />
      <Route path="/service-desk/admin/routing" element={<Navigate to="/admin/service-desk/routing" replace />} />
      <Route path="/admin/service-desk/sla" element={<ServiceDeskRoute><ServiceDeskSlaAdminRoute><ServiceDeskAdminLayout><ServiceDeskAdminSlaPage /></ServiceDeskAdminLayout></ServiceDeskSlaAdminRoute></ServiceDeskRoute>} />
      <Route path="/admin/service-desk/calendars" element={<Navigate to="/admin/service-desk/sla?section=calendars" replace />} />
      <Route path="/service-desk/admin/sla" element={<Navigate to="/admin/service-desk/sla" replace />} />
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
