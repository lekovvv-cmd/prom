import type { ComponentType } from "react";

export type PlatformModuleNavigationItem = {
  id: string;
  title: string;
  path: string;
  requiredPermissions?: string[];
};

export type PlatformModuleManifest = {
  id: string;
  title: string;
  description?: string;
  basePath: string;
  routePrefixes: string[];
  requiredPermissions: string[];
  loadRoutes: () => Promise<{ default: ComponentType }>;
  navigation: PlatformModuleNavigationItem[];
};
