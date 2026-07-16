import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { getPlatformModule } from "../modules/registry";
import { LoginPage } from "../../pages/login/ui/LoginPage";
import { ModuleSelectorPage } from "../../pages/module-selector/ui/ModuleSelectorPage";
import { ProfilePage } from "../../pages/profile/ui/ProfilePage";
import { Spinner } from "../../shared/ui/Spinner";

function ModuleRoute({ moduleId }: { moduleId: string }) {
  const manifest = getPlatformModule(moduleId);
  if (!manifest) return <Navigate to="/" replace />;
  const RoutesComponent = lazy(manifest.loadRoutes);
  return <Suspense fallback={<Spinner label={`Загружаем модуль ${manifest.title}`} />}><RoutesComponent /></Suspense>;
}

export function AppRouter() {
  return <Routes>
    <Route path="/" element={<ModuleSelectorPage />} />
    <Route path="/login" element={<LoginPage />} />
    <Route path="/profile" element={<ProfilePage />} />
    <Route path="/projects/*" element={<ModuleRoute moduleId="projects" />} />
    <Route path="/my/projects/*" element={<ModuleRoute moduleId="projects" />} />
    <Route path="/my/responses" element={<ModuleRoute moduleId="projects" />} />
    <Route path="/admin" element={<ModuleRoute moduleId="projects" />} />
    <Route path="/admin/projects/*" element={<ModuleRoute moduleId="projects" />} />
    <Route path="/admin/responses" element={<ModuleRoute moduleId="projects" />} />
    <Route path="/admin/stats" element={<ModuleRoute moduleId="projects" />} />
    <Route path="/service-desk/*" element={<ModuleRoute moduleId="service-desk" />} />
    <Route path="/admin/service-desk/*" element={<ModuleRoute moduleId="service-desk" />} />
    <Route path="*" element={<Navigate to="/projects" replace />} />
  </Routes>;
}
