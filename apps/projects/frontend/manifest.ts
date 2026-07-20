import type { PlatformModuleManifest } from "@prom/platform-contracts";

export const projectsManifest: PlatformModuleManifest = {
  id: "projects",
  title: "Проекты",
  description: "Проектные инициативы, команды, отклики и отчётность",
  basePath: "/projects",
  routePrefixes: [
    "/projects",
    "/my/projects",
    "/my/responses",
    "/profile",
    "/admin/projects",
    "/admin/responses",
    "/admin/stats",
    "/admin",
  ],
  requiredPermissions: ["projects.access"],
  loadRoutes: () => import("./routes"),
  navigation: [
    {
      id: "projects",
      title: "Проекты",
      path: "/projects",
      requiredPermissions: ["projects.access"],
    },
    {
      id: "my-projects",
      title: "Мои проекты",
      path: "/my/projects",
      requiredPermissions: ["projects.access"],
    },
  ],
};
