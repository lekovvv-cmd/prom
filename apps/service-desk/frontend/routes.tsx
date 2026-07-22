import { lazy } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { useAuth } from "@prom/auth";
import { Header, HeaderToolsProvider } from "@prom/layout";
import {
  ServiceDeskAccessProvider,
  useServiceDeskAccess,
} from "./providers/ServiceDeskAccessProvider";
import { getServiceDeskAdminLanding } from "./entities/service-desk-admin/model/adminLanding";
import type { ServiceDeskAdminConfigSection } from "./pages/service-desk-admin-configuration/ui/ServiceDeskAdminConfigurationPage";
import { Card } from "@prom/ui/Card";
import { PageLayout } from "@prom/ui/PageLayout";
import { Spinner } from "@prom/ui/Spinner";
import { ServiceDeskAdminLayout } from "./widgets/service-desk-admin-layout/ui/ServiceDeskAdminLayout";
import { ServiceDeskNotificationCenter } from "./widgets/service-desk-notifications/ui/ServiceDeskNotificationCenter";
import { ServiceDeskContextualCounters } from "./widgets/service-desk-notifications/ui/ServiceDeskContextualCounters";
import "@prom/ui/styles.css";
import "./styles/index.css";

const ServiceDeskAdminAccessPage = lazy(() =>
  import("./pages/service-desk-admin-access/ui/ServiceDeskAdminAccessPage").then(
    (module) => ({ default: module.ServiceDeskAdminAccessPage }),
  ),
);
const ServiceDeskAdminConfigurationPage = lazy(() =>
  import("./pages/service-desk-admin-configuration/ui/ServiceDeskAdminConfigurationPage").then(
    (module) => ({ default: module.ServiceDeskAdminConfigurationPage }),
  ),
);
const ServiceDeskAdminDashboardPage = lazy(() =>
  import("./pages/service-desk-admin-dashboard/ui/ServiceDeskAdminDashboardPage").then(
    (module) => ({ default: module.ServiceDeskAdminDashboardPage }),
  ),
);
const ServiceDeskAdminRoutingPage = lazy(() =>
  import("./pages/service-desk-admin-routing/ui/ServiceDeskAdminRoutingPage").then(
    (module) => ({ default: module.ServiceDeskAdminRoutingPage }),
  ),
);
const ServiceDeskAdminSlaPage = lazy(() =>
  import("./pages/service-desk-admin-sla/ui/ServiceDeskAdminSlaPage").then(
    (module) => ({ default: module.ServiceDeskAdminSlaPage }),
  ),
);
const ServiceDeskCatalogPage = lazy(() =>
  import("./pages/service-desk-catalog/ui/ServiceDeskCatalogPage").then(
    (module) => ({ default: module.ServiceDeskCatalogPage }),
  ),
);
const ServiceDeskMyTicketsPage = lazy(() =>
  import("./pages/service-desk-my-tickets/ui/ServiceDeskMyTicketsPage").then(
    (module) => ({ default: module.ServiceDeskMyTicketsPage }),
  ),
);
const ServiceDeskServiceFormPage = lazy(() =>
  import("./pages/service-desk-service-form/ui/ServiceDeskServiceFormPage").then(
    (module) => ({ default: module.ServiceDeskServiceFormPage }),
  ),
);
const ServiceDeskTicketDetailsPage = lazy(() =>
  import("./pages/service-desk-ticket-details/ui/ServiceDeskTicketDetailsPage").then(
    (module) => ({ default: module.ServiceDeskTicketDetailsPage }),
  ),
);
const ServiceDeskWorkbenchPage = lazy(() =>
  import("./pages/service-desk-workbench/ui/ServiceDeskWorkbenchPage").then(
    (module) => ({ default: module.ServiceDeskWorkbenchPage }),
  ),
);

function ServiceDeskRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const { error, isLoading, user } = useServiceDeskAccess();
  const location = useLocation();
  if (isAuthLoading || isLoading)
    return <Spinner label="Проверяем доступ к Service Desk" />;
  if (!isAuthenticated)
    return (
      <Navigate
        to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`}
        replace
      />
    );
  if (!user)
    return (
      <>
        <Header />
        <PageLayout title="Service Desk">
          <Card>
            <h3>Нет доступа</h3>
            <p className="muted">
              {error ?? "У вашей учётной записи нет доступа к Service Desk."}
            </p>
            <Link className="button button-secondary" to="/projects">
              Вернуться к проектам
            </Link>
          </Card>
        </PageLayout>
      </>
    );
  return <>{children}</>;
}

function CapabilityRoute({
  children,
  capability,
}: {
  children: React.ReactNode;
  capability: string;
}) {
  const { user } = useServiceDeskAccess();
  const allowed =
    user?.access_type === "service_desk_admin" ||
    user?.capabilities.includes(capability);
  return allowed ? children : <Navigate to="/projects" replace />;
}

function AdminIndexRoute() {
  const { user } = useServiceDeskAccess();
  const landing = getServiceDeskAdminLanding(user);
  if (!landing) return <Navigate to="/projects" replace />;
  if (landing !== "/admin/service-desk")
    return <Navigate to={landing} replace />;
  return (
    <ServiceDeskAdminLayout>
      <ServiceDeskAdminDashboardPage />
    </ServiceDeskAdminLayout>
  );
}

function ServiceDeskHeaderTools({ children }: { children: React.ReactNode }) {
  const { user } = useServiceDeskAccess();
  return (
    <HeaderToolsProvider
      tools={
        user ? (
          <>
            <ServiceDeskContextualCounters interactive />
            <ServiceDeskNotificationCenter />
          </>
        ) : null
      }
    >
      {children}
    </HeaderToolsProvider>
  );
}

function RoutedServiceDesk() {
  const { isAuthenticated } = useAuth();
  return (
    <ServiceDeskAccessProvider isAuthenticated={isAuthenticated}>
      <ServiceDeskHeaderTools>
        <Routes>
          <Route
            path="/service-desk"
            element={
              <ServiceDeskRoute>
                <ServiceDeskCatalogPage />
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/service-desk/catalog"
            element={
              <ServiceDeskRoute>
                <ServiceDeskCatalogPage />
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/service-desk/services/:serviceId"
            element={
              <ServiceDeskRoute>
                <ServiceDeskServiceFormPage />
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/service-desk/tickets/:ticketId/edit"
            element={
              <ServiceDeskRoute>
                <ServiceDeskServiceFormPage />
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/service-desk/my-tickets"
            element={
              <ServiceDeskRoute>
                <ServiceDeskMyTicketsPage />
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/service-desk/tickets"
            element={
              <ServiceDeskRoute>
                <ServiceDeskMyTicketsPage />
              </ServiceDeskRoute>
            }
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
            path="/service-desk/workbench"
            element={
              <ServiceDeskRoute>
                <CapabilityRoute capability="service_desk.assign">
                  <Header />
                  <ServiceDeskWorkbenchPage />
                </CapabilityRoute>
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/admin/service-desk"
            element={
              <ServiceDeskRoute>
                <AdminIndexRoute />
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/admin/service-desk/access"
            element={
              <ServiceDeskRoute>
                <CapabilityRoute capability="service_desk.manage_access">
                  <ServiceDeskAdminLayout>
                    <ServiceDeskAdminAccessPage />
                  </ServiceDeskAdminLayout>
                </CapabilityRoute>
              </ServiceDeskRoute>
            }
          />
          {(
            [
              "catalog",
              "templates",
              "dictionaries",
              "approvals",
            ] as ServiceDeskAdminConfigSection[]
          ).map((section) => (
            <Route
              key={section}
              path={`/admin/service-desk/${section}`}
              element={
                <ServiceDeskRoute>
                  <CapabilityRoute
                    capability={
                      section === "catalog"
                        ? "service_desk.manage_catalog"
                        : section === "approvals"
                          ? "service_desk.manage_approval_workflows"
                          : "service_desk.manage_templates"
                    }
                  >
                    <ServiceDeskAdminLayout>
                      <ServiceDeskAdminConfigurationPage section={section} />
                    </ServiceDeskAdminLayout>
                  </CapabilityRoute>
                </ServiceDeskRoute>
              }
            />
          ))}
          <Route
            path="/admin/service-desk/routing"
            element={
              <ServiceDeskRoute>
                <CapabilityRoute capability="service_desk.manage_routing">
                  <ServiceDeskAdminLayout>
                    <ServiceDeskAdminRoutingPage />
                  </ServiceDeskAdminLayout>
                </CapabilityRoute>
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/admin/service-desk/tickets"
            element={
              <ServiceDeskRoute>
                <CapabilityRoute capability="service_desk.assign">
                  <ServiceDeskAdminLayout>
                    <ServiceDeskWorkbenchPage />
                  </ServiceDeskAdminLayout>
                </CapabilityRoute>
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/admin/service-desk/sla"
            element={
              <ServiceDeskRoute>
                <CapabilityRoute capability="service_desk.manage_sla">
                  <ServiceDeskAdminLayout>
                    <ServiceDeskAdminSlaPage />
                  </ServiceDeskAdminLayout>
                </CapabilityRoute>
              </ServiceDeskRoute>
            }
          />
          <Route
            path="/admin/service-desk/calendars"
            element={<Navigate to="/admin/service-desk/sla" replace />}
          />
          <Route
            path="/service-desk/admin/routing"
            element={<Navigate to="/admin/service-desk/routing" replace />}
          />
          <Route
            path="/service-desk/admin/sla"
            element={<Navigate to="/admin/service-desk/sla" replace />}
          />
        </Routes>
      </ServiceDeskHeaderTools>
    </ServiceDeskAccessProvider>
  );
}

export default function ServiceDeskRoutes() {
  return <RoutedServiceDesk />;
}
