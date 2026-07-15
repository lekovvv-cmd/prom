import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { expect, test } from "vitest";

import { buildCatalogGroups, ServiceDeskCatalogServiceCard } from "./ServiceDeskCatalogPage";

test("groups only categories that have services and keeps uncategorized services reachable", () => {
  const categories = [
    { id: "category-1", title: "Первая", description: null, parent_id: null, position: 0, is_active: true, deleted_at: null },
    { id: "category-2", title: "Пустая", description: null, parent_id: null, position: 1, is_active: true, deleted_at: null }
  ];
  const services = [
    { id: "service-1", category_id: "category-1", title: "Услуга", short_description: null, description: null, position: 0, is_active: true, deleted_at: null, category: null },
    { id: "service-2", category_id: "missing", title: "Другая", short_description: null, description: null, position: 1, is_active: true, deleted_at: null, category: null }
  ];

  expect(buildCatalogGroups(categories, services).map((group) => [group.title, group.services.length])).toEqual([
    ["Первая", 1],
    ["Другие услуги", 1]
  ]);
});

test("shows an active service before its form is published without making it clickable", () => {
  const html = renderToStaticMarkup(
    <MemoryRouter>
      <ServiceDeskCatalogServiceCard
        service={{
          id: "service-1",
          category_id: "category-1",
          title: "Новая услуга",
          short_description: null,
          description: null,
          position: 0,
          is_active: true,
          deleted_at: null,
          category: null,
          request_form_available: false
        }}
      />
    </MemoryRouter>
  );

  expect(html).toContain("Новая услуга");
  expect(html).toContain("Форма настраивается");
  expect(html).toContain("Заявка пока недоступна");
  expect(html).not.toContain("/service-desk/services/service-1");
});
