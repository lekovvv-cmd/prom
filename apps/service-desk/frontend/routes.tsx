import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { useAuth } from "../../platform-shell/src/app/providers/AppProviders";
import { ServiceDeskAccessProvider, useServiceDeskAccess } from "../../platform-shell/src/app/providers/ServiceDeskAccessProvider";
import { getServiceDeskAdminLanding } from "../../platform-shell/src/entities/service-desk-admin/model/adminLanding";
import { ServiceDeskAdminAccessPage } from "../../platform-shell/src/pages/service-desk-admin-access/ui/ServiceDeskAdminAccessPage";
import { ServiceDeskAdminConfigurationPage, type ServiceDeskAdminConfigSection } from "../../platform-shell/src/pages/service-desk-admin-configuration/ui/ServiceDeskAdminConfigurationPage";
import { ServiceDeskAdminDashboardPage } from "../../platform-shell/src/pages/service-desk-admin-dashboard/ui/ServiceDeskAdminDashboardPage";
import { ServiceDeskAdminRoutingPage } from "../../platform-shell/src/pages/service-desk-admin-routing/ui/ServiceDeskAdminRoutingPage";
import { ServiceDeskAdminSlaPage } from "../../platform-shell/src/pages/service-desk-admin-sla/ui/ServiceDeskAdminSlaPage";
import { ServiceDeskCatalogPage } from "../../platform-shell/src/pages/service-desk-catalog/ui/ServiceDeskCatalogPage";
import { ServiceDeskMyTicketsPage } from "../../platform-shell/src/pages/service-desk-my-tickets/ui/ServiceDeskMyTicketsPage";
import { ServiceDeskServiceFormPage } from "../../platform-shell/src/pages/service-desk-service-form/ui/ServiceDeskServiceFormPage";
import { ServiceDeskTicketDetailsPage } from "../../platform-shell/src/pages/service-desk-ticket-details/ui/ServiceDeskTicketDetailsPage";
import { ServiceDeskWorkbenchPage } from "../../platform-shell/src/pages/service-desk-workbench/ui/ServiceDeskWorkbenchPage";
import { Card } from "../../platform-shell/src/shared/ui/Card";
import { PageLayout } from "../../platform-shell/src/shared/ui/PageLayout";
import { Spinner } from "../../platform-shell/src/shared/ui/Spinner";
import { Header } from "../../platform-shell/src/widgets/header/ui/Header";
import { ServiceDeskAdminLayout } from "../../platform-shell/src/widgets/service-desk-admin-layout/ui/ServiceDeskAdminLayout";

function ServiceDeskRoute({ children }: { children: React.ReactNode }) {
  const { isLoading: isAuthLoading, token } = useAuth();
  const { error, isLoading, user } = useServiceDeskAccess();
  const location = useLocation();
  if (isAuthLoading || isLoading) return <Spinner label="Проверяем доступ к Service Desk" />;
  if (!token) return <Navigate to={`/login?next=${encodeURIComponent(location.pathname + location.search)}`} replace />;
  if (!user) return <><Header /><PageLayout title="Service Desk"><Card><h3>Нет доступа</h3><p className="muted">{error ?? "У вашей учётной записи нет доступа к Service Desk."}</p><Link className="button button-secondary" to="/projects">Вернуться к проектам</Link></Card></PageLayout></>;
  return <>{children}</>;
}

function CapabilityRoute({ children, capability }: { children: React.ReactNode; capability: string }) {
  const { user } = useServiceDeskAccess();
  const allowed = user?.access_type === "service_desk_admin" || user?.capabilities.includes(capability);
  return allowed ? children : <Navigate to="/projects" replace />;
}

function AdminIndexRoute() {
  const { user } = useServiceDeskAccess();
  const landing = getServiceDeskAdminLanding(user);
  if (!landing) return <Navigate to="/projects" replace />;
  if (landing !== "/admin/service-desk") return <Navigate to={landing} replace />;
  return <ServiceDeskAdminLayout><ServiceDeskAdminDashboardPage /></ServiceDeskAdminLayout>;
}

function RoutedServiceDesk() {
  const { token } = useAuth();
  return <ServiceDeskAccessProvider token={token}><Routes>
    <Route path="/service-desk" element={<ServiceDeskRoute><ServiceDeskCatalogPage /></ServiceDeskRoute>} />
    <Route path="/service-desk/catalog" element={<ServiceDeskRoute><ServiceDeskCatalogPage /></ServiceDeskRoute>} />
    <Route path="/service-desk/services/:serviceId" element={<ServiceDeskRoute><ServiceDeskServiceFormPage /></ServiceDeskRoute>} />
    <Route path="/service-desk/tickets/:ticketId/edit" element={<ServiceDeskRoute><ServiceDeskServiceFormPage /></ServiceDeskRoute>} />
    <Route path="/service-desk/my-tickets" element={<ServiceDeskRoute><ServiceDeskMyTicketsPage /></ServiceDeskRoute>} />
    <Route path="/service-desk/tickets" element={<ServiceDeskRoute><ServiceDeskMyTicketsPage /></ServiceDeskRoute>} />
    <Route path="/service-desk/tickets/:ticketId" element={<ServiceDeskRoute><ServiceDeskTicketDetailsPage /></ServiceDeskRoute>} />
    <Route path="/service-desk/workbench" element={<ServiceDeskRoute><CapabilityRoute capability="service_desk.assign"><Header /><ServiceDeskWorkbenchPage /></CapabilityRoute></ServiceDeskRoute>} />
    <Route path="/admin/service-desk" element={<ServiceDeskRoute><AdminIndexRoute /></ServiceDeskRoute>} />
    <Route path="/admin/service-desk/access" element={<ServiceDeskRoute><CapabilityRoute capability="service_desk.manage_access"><ServiceDeskAdminLayout><ServiceDeskAdminAccessPage /></ServiceDeskAdminLayout></CapabilityRoute></ServiceDeskRoute>} />
    {(["catalog", "templates", "dictionaries", "approvals"] as ServiceDeskAdminConfigSection[]).map((section) => <Route key={section} path={`/admin/service-desk/${section}`} element={<ServiceDeskRoute><CapabilityRoute capability={section === "catalog" ? "service_desk.manage_catalog" : section === "approvals" ? "service_desk.manage_approval_workflows" : "service_desk.manage_templates"}><ServiceDeskAdminLayout><ServiceDeskAdminConfigurationPage section={section} /></ServiceDeskAdminLayout></CapabilityRoute></ServiceDeskRoute>} />)}
    <Route path="/admin/service-desk/routing" element={<ServiceDeskRoute><CapabilityRoute capability="service_desk.manage_routing"><ServiceDeskAdminLayout><ServiceDeskAdminRoutingPage /></ServiceDeskAdminLayout></CapabilityRoute></ServiceDeskRoute>} />
    <Route path="/admin/service-desk/tickets" element={<ServiceDeskRoute><CapabilityRoute capability="service_desk.assign"><ServiceDeskAdminLayout><ServiceDeskWorkbenchPage /></ServiceDeskAdminLayout></CapabilityRoute></ServiceDeskRoute>} />
    <Route path="/admin/service-desk/sla" element={<ServiceDeskRoute><CapabilityRoute capability="service_desk.manage_sla"><ServiceDeskAdminLayout><ServiceDeskAdminSlaPage /></ServiceDeskAdminLayout></CapabilityRoute></ServiceDeskRoute>} />
    <Route path="/admin/service-desk/calendars" element={<Navigate to="/admin/service-desk/sla" replace />} />
    <Route path="/service-desk/admin/routing" element={<Navigate to="/admin/service-desk/routing" replace />} />
    <Route path="/service-desk/admin/sla" element={<Navigate to="/admin/service-desk/sla" replace />} />
  </Routes></ServiceDeskAccessProvider>;
}

export default function ServiceDeskRoutes() { return <RoutedServiceDesk />; }

