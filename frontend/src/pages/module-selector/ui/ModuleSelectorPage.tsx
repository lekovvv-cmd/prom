import { ArrowUp, FolderKanban, Table2 } from "lucide-react";
import { Link } from "react-router-dom";

import { Header } from "../../../widgets/header/ui/Header";

export function ModuleSelectorPage() {
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
            <Link className="module-selector-card" to="/projects">
              <span className="module-selector-icon"><FolderKanban size={28} aria-hidden="true" /></span>
              <span className="module-selector-card-copy">
                <strong>Проектный модуль</strong>
                <span>Проекты, инициативы, команды, отклики и отчётность.</span>
              </span>
              <ArrowUp size={20} aria-hidden="true" />
            </Link>
            <Link className="module-selector-card" to="/service-desk">
              <span className="module-selector-icon"><Table2 size={28} aria-hidden="true" /></span>
              <span className="module-selector-card-copy">
                <strong>Service Desk</strong>
                <span>Каталог услуг, заявки, согласования, исполнение и SLA.</span>
              </span>
              <ArrowUp size={20} aria-hidden="true" />
            </Link>
          </div>
        </section>
      </main>
    </>
  );
}
