import type { PlatformModuleManifest } from "@prom/platform-contracts";

import { projectsManifest } from "../../../../projects/frontend/manifest";
import { serviceDeskManifest } from "../../../../service-desk/frontend/manifest";

export const platformModules: readonly PlatformModuleManifest[] = [
  projectsManifest,
  serviceDeskManifest,
];

export function getPlatformModule(
  id: string,
): PlatformModuleManifest | undefined {
  return platformModules.find((module) => module.id === id);
}

export function getPlatformModuleForPath(
  pathname: string,
): PlatformModuleManifest | undefined {
  return platformModules
    .flatMap((manifest) =>
      manifest.routePrefixes.map((prefix) => ({ manifest, prefix })),
    )
    .filter(
      ({ prefix }) => pathname === prefix || pathname.startsWith(`${prefix}/`),
    )
    .sort((left, right) => right.prefix.length - left.prefix.length)
    .at(0)?.manifest;
}
