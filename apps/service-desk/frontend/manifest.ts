import type { PlatformModuleManifest } from "@prom/platform-contracts";

export const serviceDeskManifest: PlatformModuleManifest = {
  id: "service-desk",
  title: "Service Desk",
  description: "Каталог услуг, заявки, согласования и SLA",
  basePath: "/service-desk",
  routePrefixes: ["/service-desk", "/admin/service-desk"],
  requiredPermissions: ["service_desk.access"],
  loadRoutes: () => import("./routes"),
  navigation: [
    {
      id: "service-desk",
      title: "Service Desk",
      path: "/service-desk",
      requiredPermissions: ["service_desk.access"],
    },
    {
      id: "my-tickets",
      title: "Мои заявки",
      path: "/service-desk/my-tickets",
      requiredPermissions: ["service_desk.access"],
    },
  ],
};
