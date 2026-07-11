import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, Table2, Ticket } from "lucide-react";

import { getServiceDeskCategories, getServiceDeskServices } from "../../../entities/service-desk-catalog/api/serviceDeskCatalogApi";
import type { ServiceDeskCategory, ServiceDeskService } from "../../../entities/service-desk-catalog/model/types";
import { Card } from "../../../shared/ui/Card";
import { Input } from "../../../shared/ui/Input";
import { PageLayout } from "../../../shared/ui/PageLayout";
import { Spinner } from "../../../shared/ui/Spinner";
import { Header } from "../../../widgets/header/ui/Header";

export function ServiceDeskCatalogPage() {
  const [query, setQuery] = useState("");
  const [categories, setCategories] = useState<ServiceDeskCategory[]>([]);
  const [services, setServices] = useState<ServiceDeskService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    Promise.all([getServiceDeskCategories(query), getServiceDeskServices("", query)])
      .then(([categoryItems, serviceItems]) => {
        if (!active) return;
        setCategories(categoryItems.filter((item) => item.is_active && !item.deleted_at));
        setServices(serviceItems.filter((item) => item.is_active && !item.deleted_at));
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Не удалось загрузить каталог");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [query]);

  const categoryMap = useMemo(() => new Map(categories.map((category) => [category.id, category])), [categories]);
  const groupedServices = useMemo(() => categories.map((category) => ({ category, services: services.filter((service) => service.category_id === category.id) })).filter((group) => group.services.length > 0), [categories, services]);
  const uncategorized = services.filter((service) => !categoryMap.has(service.category_id));

  return (
    <>
      <Header />
      <PageLayout title="Каталог Service Desk" subtitle="Выберите услугу, чтобы создать заявку. Каталог доступен без входа.">
        <div className="service-desk-catalog-toolbar">
          <Input label="Поиск услуги или категории" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Например, доступ к системе" />
          <Link className="button button-secondary" to="/service-desk/my-tickets"><Ticket size={16} aria-hidden="true" />Мои заявки</Link>
        </div>
        {loading ? <Spinner label="Загружаем каталог" /> : error ? <Card><p className="form-error" role="alert">{error}</p></Card> : groupedServices.length || uncategorized.length ? (
          <div className="service-desk-catalog-groups">
            {groupedServices.map(({ category, services: categoryServices }) => (
              <section key={category.id} className="service-desk-catalog-group" aria-labelledby={`category-${category.id}`}>
                <div className="section-heading"><div><span className="service-desk-eyebrow"><Table2 size={14} aria-hidden="true" /> Категория</span><h2 id={`category-${category.id}`}>{category.title}</h2></div><p>{category.description}</p></div>
                <div className="service-desk-service-grid">{categoryServices.map((service) => <ServiceCard key={service.id} service={service} />)}</div>
              </section>
            ))}
            {uncategorized.length ? <section className="service-desk-catalog-group"><div className="section-heading"><h2>Другие услуги</h2></div><div className="service-desk-service-grid">{uncategorized.map((service) => <ServiceCard key={service.id} service={service} />)}</div></section> : null}
          </div>
        ) : <Card><div className="empty-state"><Search size={22} aria-hidden="true" /><h3>Ничего не найдено</h3><p>Измените запрос или попробуйте поискать позже.</p></div></Card>}
      </PageLayout>
    </>
  );
}

function ServiceCard({ service }: { service: ServiceDeskService }) {
  return <Card className="service-desk-service-card"><div><span className="service-desk-eyebrow">Услуга</span><h3>{service.title}</h3><p>{service.short_description ?? service.description ?? "Описание услуги появится здесь."}</p></div><Link className="button" to={`/service-desk/services/${service.id}`}>Открыть услугу</Link></Card>;
}
