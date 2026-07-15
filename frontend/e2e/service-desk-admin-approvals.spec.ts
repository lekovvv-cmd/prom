import { expect, test } from "@playwright/test";

import { createCatalogFixtureCleaner, loginAs, watchPage } from "./helpers";

const catalogFixtures = createCatalogFixtureCleaner();

test.afterEach(async ({ page }) => {
  await catalogFixtures.cleanup(page);
});

test("загрузка услуг в согласованиях показывает понятную ошибку и повторяется", async ({ page }) => {
  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/approvals");
  await page.route("**/service-desk-api/admin/services", async (route) => {
    if (route.request().method() === "GET") await route.abort("failed");
    else await route.continue();
  });
  await page.reload();
  await expect(page.getByRole("alert")).toContainText("Не удалось связаться с сервером. Проверьте подключение и попробуйте ещё раз.");
  await expect(page.getByRole("button", { name: "Повторить" })).toBeVisible();
  await expect(page.getByRole("alert")).not.toContainText("Failed to fetch");
  await page.unroute("**/service-desk-api/admin/services");
  await page.getByRole("button", { name: "Повторить" }).click();
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect.poll(async () => page.getByLabel("Услуга").locator("option").count()).toBeGreaterThan(1);
});

test("администратор включает, изменяет и отключает согласование у услуги", async ({ page }) => {
  const diagnostics = watchPage(page);
  const suffix = Date.now();
  const categoryTitle = `Approval QA category ${suffix}`;
  const serviceTitle = `Approval QA service ${suffix}`;
  const stageTitle = `Approval QA stage ${suffix}`;
  const editedStageTitle = `${stageTitle} updated`;

  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/catalog");
  await catalogFixtures.track(page, { categoryTitles: [categoryTitle], serviceTitles: [serviceTitle] });
  const categories = page.locator(".card").filter({ has: page.getByRole("heading", { name: "Категории" }) });
  await categories.getByLabel("Новая категория").fill(categoryTitle);
  await categories.getByRole("button", { name: "Создать" }).click();
  const services = page.locator(".card").filter({ has: page.getByRole("heading", { name: "Услуги" }) });
  await services.getByLabel("Новая услуга").fill(serviceTitle);
  await services.getByLabel("Категория").selectOption({ label: categoryTitle });
  await services.getByRole("button", { name: "Создать" }).click();

  await page.goto("/admin/service-desk/templates");
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  await page.getByRole("button", { name: "Создать новую версию" }).click();
  await page.getByRole("button", { name: "Опубликовать версию" }).click();

  await page.goto("/admin/service-desk/approvals");
  await expect(page.getByRole("heading", { name: "Согласования" })).toBeVisible();
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  await expect(page.getByText("Опубликованная версия 1")).toBeVisible();
  await expect(page.getByText("Изменения применятся только к новым заявкам.")).toBeVisible();
  await expect(page.getByLabel("Версия формы")).toHaveCount(0);

  await page.getByRole("button", { name: "Включить согласование" }).click();
  await page.getByLabel("Название нового этапа").fill(stageTitle);
  await page.getByLabel("Правило нового этапа").selectOption("any");
  await page.getByRole("button", { name: "Добавить этап" }).click();
  await expect(page.getByLabel("Правило этапа 1")).toHaveValue("any");
  await page.getByLabel("Добавить согласующего к этапу 1").selectOption({ index: 1 });
  await page.getByRole("button", { name: "Добавить согласующего" }).click();
  await expect(page.locator(".tag")).toHaveCount(1);
  await page.getByRole("button", { name: "Сохранить и применить" }).click();
  await expect(page.getByText("Версия 2 опубликована. Предыдущая версия перенесена в архив.")).toBeVisible();
  await expect(page.getByText("Опубликованная версия 2")).toBeVisible();

  await page.getByLabel("Название этапа 1").fill(editedStageTitle);
  await page.getByRole("button", { name: "Сохранить и применить" }).click();
  await expect(page.getByText("Версия 3 опубликована. Предыдущая версия перенесена в архив.")).toBeVisible();
  await expect(page.getByLabel("Название этапа 1")).toHaveValue(editedStageTitle);

  await page.getByRole("button", { name: "Отключить согласование" }).click();
  await expect(page.getByText("Новые заявки будут создаваться без согласования.")).toBeVisible();
  await page.getByRole("button", { name: "Сохранить и применить" }).click();
  await expect(page.getByText("Версия 4 опубликована. Предыдущая версия перенесена в архив.")).toBeVisible();
  await expect(page.getByText("Опубликованная версия 4")).toBeVisible();

  diagnostics.assertClean();
});
