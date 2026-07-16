import { expect, test } from "@playwright/test";

import { attachScreenshot, createCatalogFixtureCleaner, loginAs, watchPage } from "./helpers";

const catalogFixtures = createCatalogFixtureCleaner();

test.afterEach(async ({ page }) => {
  await catalogFixtures.cleanup(page);
});

test("admin catalog CRUD validates duplicate category titles", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  const suffix = Date.now();
  const title = `Browser QA category ${suffix}`;
  const editedTitle = `${title} edited`;
  const serviceTitle = `Browser QA service ${suffix}`;

  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/catalog");
  await catalogFixtures.track(page, {
    categoryTitles: [title, editedTitle],
    serviceTitles: [serviceTitle]
  });
  await expect(page.getByRole("heading", { name: "Каталог Service Desk" })).toBeVisible();

  const categories = page.locator(".card").filter({
    has: page.getByRole("heading", { name: "Категории" })
  });
  await categories.getByLabel("Новая категория").fill(title);
  await categories.getByRole("button", { name: "Создать" }).click();
  let categoryRow = categories.locator(".admin-config-row").filter({ hasText: title });
  await expect(categoryRow).toBeVisible();

  await categoryRow.getByRole("button", { name: "Изменить" }).click();
  categoryRow = categories.locator(".admin-config-row").filter({
    has: page.getByLabel("Название", { exact: true })
  });
  await categoryRow.getByLabel("Название").fill(editedTitle);
  await categoryRow.getByLabel("Описание").fill("Создано browser QA через production UI");
  await categoryRow.getByRole("button", { name: "Сохранить" }).click();
  categoryRow = categories.locator(".admin-config-row").filter({ hasText: editedTitle });
  await expect(categoryRow).toContainText("Активна");

  const services = page.locator(".card").filter({
    has: page.getByRole("heading", { name: "Услуги" })
  });
  await services.getByLabel("Новая услуга").fill(serviceTitle);
  await services.getByLabel("Категория").selectOption({ label: editedTitle });
  await services.getByRole("button", { name: "Создать" }).click();
  await expect(services.locator(".admin-config-row").filter({ hasText: serviceTitle })).toBeVisible();

  await categoryRow.getByRole("button", { name: "Выключить" }).click();
  await expect(categoryRow).toContainText("Выключена");
  await categoryRow.getByRole("button", { name: "Восстановить" }).click();
  await expect(categoryRow).toContainText("Активна");

  await categories.getByLabel("Новая категория").fill(editedTitle.toUpperCase());
  await categories.getByRole("button", { name: "Создать" }).click();
  await expect(page.getByRole("alert")).toContainText("уже существует");
  await expect(categories.locator(".admin-config-row").filter({ hasText: editedTitle })).toHaveCount(1);

  await page.reload();
  await expect(categories.locator(".admin-config-row").filter({ hasText: editedTitle })).toBeVisible();
  await expect(services.locator(".admin-config-row").filter({ hasText: serviceTitle })).toBeVisible();
  await attachScreenshot(page, testInfo, "catalog-admin");
  diagnostics.assertClean(
    (value) => value.startsWith("409 POST "),
    (value) => value.includes("409 (Conflict)")
  );
});
