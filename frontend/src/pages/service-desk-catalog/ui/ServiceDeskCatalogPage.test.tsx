import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { expect, test } from "vitest";

import { ServiceDeskCatalogServiceCard } from "./ServiceDeskCatalogPage";

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
