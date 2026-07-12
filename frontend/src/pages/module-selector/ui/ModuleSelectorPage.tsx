import { ArrowUp, FolderKanban, Table2 } from "lucide-react";
import { Link } from "react-router-dom";

import { useAuth } from "../../../app/providers/AppProviders";
import { useServiceDeskAccess } from "../../../app/providers/ServiceDeskAccessProvider";
import { Header } from "../../../widgets/header/ui/Header";

export function ModuleSelectorPage() {
  const { token } = useAuth();
  const { isLoading, user: serviceDeskUser } = useServiceDeskAccess();
  const projectsTarget = token ? "/projects" : "/login?next=%2Fprojects";
  const serviceDeskTarget = token ? "/service-desk" : "/login?next=%2Fservice-desk";

  return (
    <>
      <Header />
      <main className="module-selector-page">
        <section className="module-selector" aria-labelledby="module-selector-title">
          <div className="module-selector-heading">
            <p className="eyebrow">PROM</p>
            <h1 id="module-selector-title">Выберите сервис</h1>
            <p>Единая точка входа в рабочие сервисы университета.</p>
          </div>
          <div className="module-selector-grid">
            <Link className="module-selector-card" to={projectsTarget}>
              <span className="module-selector-icon"><FolderKanban size={28} aria-hidden="true" /></span>
              <span className="module-selector-card-copy">
                <strong>Проектный модуль</strong>
                <span>Проекты, инициативы, команды, отклики и отчётность.</span>
              </span>
              <ArrowUp size={20} aria-hidden="true" />
            </Link>
            {!token || serviceDeskUser ? (
              <Link className="module-selector-card" to={serviceDeskTarget}>
                <span className="module-selector-icon"><Table2 size={28} aria-hidden="true" /></span>
                <span className="module-selector-card-copy">
                  <strong>Service Desk</strong>
                  <span>Каталог услуг, заявки, согласования, исполнение и SLA.</span>
                </span>
                <ArrowUp size={20} aria-hidden="true" />
              </Link>
            ) : (
              <div className="module-selector-card module-selector-card-disabled" aria-disabled="true">
                <span className="module-selector-icon"><Table2 size={28} aria-hidden="true" /></span>
                <span className="module-selector-card-copy">
                  <strong>Service Desk</strong>
                  <span>{isLoading ? "Проверяем доступ…" : "У вашей учётной записи нет доступа к Service Desk."}</span>
                </span>
              </div>
            )}
          </div>
        </section>
      </main>
    </>
  );
}
