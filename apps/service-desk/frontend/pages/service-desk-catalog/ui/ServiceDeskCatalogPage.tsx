import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Clock3, Search, Table2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import {
  getServiceDeskCategories,
  getServiceDeskServices,
} from "../../../entities/service-desk-catalog/api/serviceDeskCatalogApi";
import type {
  ServiceDeskCategory,
  ServiceDeskService,
} from "../../../entities/service-desk-catalog/model/types";
import { serviceDeskQueryKeys } from "../../../api/queryKeys";
import { Card } from "@prom/ui/Card";
import { Button } from "@prom/ui/Button";
import { Input } from "@prom/ui/Input";
import { PageLayout } from "@prom/ui/PageLayout";
import { Spinner } from "@prom/ui/Spinner";
import { Header } from "@prom/layout";

const uncategorizedGroupId = "__uncategorized__";

function serviceCountLabel(count: number) {
  if (count % 100 >= 11 && count % 100 <= 14) return "услуг";
  if (count % 10 === 1) return "услуга";
  if (count % 10 >= 2 && count % 10 <= 4) return "услуги";
  return "услуг";
}

type CatalogGroup = {
  id: string;
  title: string;
  description: string | null;
  services: ServiceDeskService[];
};

export function buildCatalogGroups(
  categories: ServiceDeskCategory[],
  services: ServiceDeskService[],
): CatalogGroup[] {
  const categoryIds = new Set(categories.map((category) => category.id));
  const groups = categories.map((category) => ({
    id: category.id,
    title: category.title,
    description: category.description,
    services: services.filter((service) => service.category_id === category.id),
  }));
  const uncategorized = services.filter(
    (service) => !categoryIds.has(service.category_id),
  );

  return uncategorized.length
    ? [
        ...groups,
        {
          id: uncategorizedGroupId,
          title: "Другие услуги",
          description: null,
          services: uncategorized,
        },
      ]
    : groups;
}

export function ServiceDeskCatalogPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState("");
  const selectedCategoryId = searchParams.get("category") ?? "";
  const catalogQuery = useQuery({
    queryKey: serviceDeskQueryKeys.catalog(),
    queryFn: async ({ signal }) => {
      const [categories, services] = await Promise.all([
        getServiceDeskCategories("", signal),
        getServiceDeskServices("", "", signal),
      ]);
      return {
        categories: categories.filter(
          (item) => item.is_active && !item.deleted_at,
        ),
        services: services.filter((item) => item.is_active && !item.deleted_at),
      };
    },
  });
  const categories = catalogQuery.data?.categories ?? [];
  const services = catalogQuery.data?.services ?? [];
  const error =
    catalogQuery.error instanceof Error ? catalogQuery.error.message : null;

  const categoryMap = useMemo(
    () => new Map(categories.map((category) => [category.id, category])),
    [categories],
  );
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const filteredServices = useMemo(
    () =>
      !normalizedQuery
        ? services
        : services.filter((service) =>
            [
              service.title,
              service.short_description,
              service.description,
              categoryMap.get(service.category_id)?.title,
            ]
              .filter(Boolean)
              .join(" ")
              .toLocaleLowerCase()
              .includes(normalizedQuery),
          ),
    [categoryMap, normalizedQuery, services],
  );
  const allGroups = useMemo(
    () => buildCatalogGroups(categories, services),
    [categories, services],
  );
  const matchingGroups = useMemo(
    () =>
      buildCatalogGroups(categories, filteredServices).filter(
        (group) => group.services.length,
      ),
    [categories, filteredServices],
  );
  const shownGroups = selectedCategoryId
    ? allGroups.filter((group) => group.id === selectedCategoryId)
    : normalizedQuery
      ? matchingGroups
      : [];
  const selectedGroup = allGroups.find(
    (group) => group.id === selectedCategoryId,
  );
  function selectCategory(categoryId: string) {
    setQuery("");
    setSearchParams(categoryId ? { category: categoryId } : {});
  }

  return (
    <>
      <Header />
      <PageLayout
        title="Каталог Service Desk"
        subtitle="Выберите услугу, чтобы создать заявку."
      >
        <div className="service-desk-catalog-toolbar">
          <Input
            label="Поиск услуги или категории"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setSearchParams({});
            }}
            placeholder="Например, доступ к системе"
          />
        </div>
        {catalogQuery.isLoading ? (
          <Spinner label="Загружаем каталог" />
        ) : error ? (
          <Card>
            <p className="form-error" role="alert">
              {error}
            </p>
          </Card>
        ) : allGroups.length ? (
          <div className="service-desk-catalog-groups">
            <section
              className="service-desk-catalog-category-picker"
              aria-labelledby="catalog-categories-title"
            >
              <div className="service-desk-catalog-category-picker-heading">
                <div>
                  <span className="service-desk-eyebrow">
                    <Table2 size={14} aria-hidden="true" />
                    Категории
                  </span>
                  <h2 id="catalog-categories-title">Куда нужна заявка?</h2>
                  <p>
                    Выберите категорию — покажем только относящиеся к ней
                    услуги.
                  </p>
                </div>
                {selectedCategoryId ? (
                  <Button variant="ghost" onClick={() => selectCategory("")}>
                    Все категории
                  </Button>
                ) : null}
              </div>
              <div className="service-desk-catalog-category-grid">
                {allGroups.map((group) => (
                  <button
                    key={group.id}
                    type="button"
                    className={`service-desk-catalog-category-button${selectedCategoryId === group.id ? " active" : ""}`}
                    aria-pressed={selectedCategoryId === group.id}
                    onClick={() => selectCategory(group.id)}
                  >
                    <strong>{group.title}</strong>
                    <span>
                      {group.services.length}{" "}
                      {serviceCountLabel(group.services.length)}
                    </span>
                  </button>
                ))}
              </div>
            </section>

            {shownGroups.length ? (
              <div className="service-desk-catalog-results" aria-live="polite">
                <div className="service-desk-catalog-results-heading">
                  <div>
                    <span className="service-desk-eyebrow">
                      {normalizedQuery
                        ? "Результаты поиска"
                        : "Выбранная категория"}
                    </span>
                    <h2>
                      {normalizedQuery
                        ? `По запросу «${query.trim()}»`
                        : selectedGroup?.title}
                    </h2>
                    {selectedGroup?.description && !normalizedQuery ? (
                      <p>{selectedGroup.description}</p>
                    ) : null}
                  </div>
                </div>
                {shownGroups.map((group) => (
                  <section
                    key={group.id}
                    className="service-desk-catalog-group"
                    aria-labelledby={
                      normalizedQuery ? `category-${group.id}` : undefined
                    }
                  >
                    {normalizedQuery ? (
                      <h3
                        id={`category-${group.id}`}
                        className="service-desk-catalog-result-group-title"
                      >
                        {group.title}
                      </h3>
                    ) : null}
                    <div className="service-desk-service-grid">
                      {group.services.map((service) => (
                        <ServiceDeskCatalogServiceCard
                          key={service.id}
                          service={service}
                        />
                      ))}
                    </div>
                    {group.services.length === 0 ? (
                      <p className="muted">В этой категории пока нет услуг.</p>
                    ) : null}
                  </section>
                ))}
              </div>
            ) : normalizedQuery ? (
              <Card>
                <div className="empty-state">
                  <Search size={22} aria-hidden="true" />
                  <h3>Ничего не найдено</h3>
                  <p>Попробуйте другое название услуги или категории.</p>
                </div>
              </Card>
            ) : null}
          </div>
        ) : (
          <Card>
            <div className="empty-state">
              <Search size={22} aria-hidden="true" />
              <h3>Услуг пока нет</h3>
              <p>
                Когда услуги появятся в каталоге, их можно будет найти здесь.
              </p>
            </div>
          </Card>
        )}
      </PageLayout>
    </>
  );
}

export function ServiceDeskCatalogServiceCard({
  service,
}: {
  service: ServiceDeskService;
}) {
  const requestFormAvailable = service.request_form_available !== false;
  return (
    <Card className="service-desk-service-card">
      <div>
        <span className="service-desk-eyebrow">Услуга</span>
        <h3>{service.title}</h3>
        <p>
          {service.short_description ??
            service.description ??
            "Описание услуги появится здесь."}
        </p>
        {!requestFormAvailable ? (
          <p className="service-desk-service-card-status">
            <Clock3 size={15} aria-hidden="true" />
            Форма настраивается
          </p>
        ) : null}
      </div>
      {requestFormAvailable ? (
        <Link className="button" to={`/service-desk/services/${service.id}`}>
          Открыть услугу
        </Link>
      ) : (
        <span className="button button-secondary" aria-disabled="true">
          Заявка пока недоступна
        </span>
      )}
    </Card>
  );
}
