import { lazy, Suspense } from "react";
import { Navigate, useLocation } from "react-router-dom";

import {
  getPlatformModule,
  getPlatformModuleForPath,
  platformModules,
} from "../modules/registry";
import { LoginPage } from "../../pages/login/ui/LoginPage";
import { ModuleSelectorPage } from "../../pages/module-selector/ui/ModuleSelectorPage";
import { ModuleErrorBoundary } from "@prom/ui/ModuleErrorBoundary";
import { Spinner } from "@prom/ui/Spinner";

const moduleRoutes = new Map(
  platformModules.map((manifest) => [manifest.id, lazy(manifest.loadRoutes)]),
);

function ModuleRoute({ moduleId }: { moduleId: string }) {
  const manifest = getPlatformModule(moduleId);
  const RoutesComponent = moduleRoutes.get(moduleId);
  if (!manifest || !RoutesComponent) return <Navigate to="/" replace />;
  return (
    <ModuleErrorBoundary
      key={moduleId}
      moduleId={moduleId}
      moduleName={manifest.title}
    >
      <Suspense
        fallback={<Spinner label={`Загружаем модуль ${manifest.title}`} />}
      >
        <RoutesComponent />
      </Suspense>
    </ModuleErrorBoundary>
  );
}

export function AppRouter() {
  const location = useLocation();
  if (location.pathname === "/") return <ModuleSelectorPage />;
  if (location.pathname === "/login") return <LoginPage />;

  const manifest = getPlatformModuleForPath(location.pathname);
  if (manifest) return <ModuleRoute moduleId={manifest.id} />;

  return <Navigate to={platformModules[0]?.basePath ?? "/"} replace />;
}
