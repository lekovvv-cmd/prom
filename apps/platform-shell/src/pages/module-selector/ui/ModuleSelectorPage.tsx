import { ArrowUp, FolderKanban, Table2 } from "lucide-react";
import { Link } from "react-router-dom";

import { useAuth } from "@prom/auth";
import { Header } from "@prom/layout";
import { platformModules } from "../../../app/modules/registry";

const moduleIcons = {
  projects: FolderKanban,
  "service-desk": Table2,
};

const moduleCardTitles = {
  projects: "Проектный модуль",
  "service-desk": "Service Desk",
};

export function ModuleSelectorPage() {
  const { isAuthenticated, modules } = useAuth();
  const availableModules = isAuthenticated
    ? platformModules.filter((manifest) =>
        modules.some((module) => module.id === manifest.id),
      )
    : platformModules;

  return (
    <>
      <Header />
      <main className="module-selector-page">
        <section
          className="module-selector"
          aria-labelledby="module-selector-title"
        >
          <div className="module-selector-heading">
            <p className="eyebrow">PROM</p>
            <h1 id="module-selector-title">Выберите сервис</h1>
            <p>Единая точка входа в рабочие сервисы университета.</p>
          </div>
          <div className="module-selector-grid">
            {availableModules.map((manifest) => {
              const Icon =
                moduleIcons[manifest.id as keyof typeof moduleIcons] ??
                FolderKanban;
              const target = isAuthenticated
                ? manifest.basePath
                : `/login?next=${encodeURIComponent(manifest.basePath)}`;
              return (
                <Link
                  className="module-selector-card"
                  key={manifest.id}
                  to={target}
                >
                  <span className="module-selector-icon">
                    <Icon size={28} aria-hidden="true" />
                  </span>
                  <span className="module-selector-card-copy">
                    <strong>
                      {moduleCardTitles[
                        manifest.id as keyof typeof moduleCardTitles
                      ] ?? manifest.title}
                    </strong>
                    <span>{manifest.description}</span>
                  </span>
                  <ArrowUp size={20} aria-hidden="true" />
                </Link>
              );
            })}
          </div>
        </section>
      </main>
    </>
  );
}
