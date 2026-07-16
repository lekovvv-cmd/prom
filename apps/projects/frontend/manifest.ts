import type { PlatformModuleManifest } from "../../platform-shell/src/app/modules/registry";

export const projectsManifest: PlatformModuleManifest = {
  id: "projects",
  title: "Проекты",
  description: "Проектные инициативы, команды, отклики и отчётность",
  basePath: "/projects",
  requiredPermissions: ["projects.access"],
  loadRoutes: () => import("./routes"),
  navigation: [
    { id: "projects", title: "Проекты", path: "/projects", requiredPermissions: ["projects.access"] },
    { id: "my-projects", title: "Мои проекты", path: "/my/projects", requiredPermissions: ["projects.access"] },
  ],
};

