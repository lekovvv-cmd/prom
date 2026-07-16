import type { ComponentType } from "react";

import { projectsManifest } from "../../../../projects/frontend/manifest";
import { serviceDeskManifest } from "../../../../service-desk/frontend/manifest";

export type PlatformModuleManifest = {
  id: string;
  title: string;
  description?: string;
  basePath: string;
  requiredPermissions: string[];
  loadRoutes: () => Promise<{ default: ComponentType }>;
  navigation: Array<{
    id: string;
    title: string;
    path: string;
    requiredPermissions?: string[];
  }>;
};

export const platformModules: readonly PlatformModuleManifest[] = [projectsManifest, serviceDeskManifest];

export function getPlatformModule(id: string): PlatformModuleManifest | undefined {
  return platformModules.find((module) => module.id === id);
}

