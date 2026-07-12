import { expect, test } from "@playwright/test";

import { attachScreenshot, loginAs, watchPage } from "./helpers";

test("admin creates and publishes a template with production preview", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  const suffix = Date.now();
  const categoryTitle = `Template QA category ${suffix}`;
  const serviceTitle = `Template QA service ${suffix}`;
  const fieldLabel = `Contact email ${suffix}`;

  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/catalog");
  const categories = page.locator(".card").filter({ has: page.getByRole("heading", { name: "Категории" }) });
  await categories.getByLabel("Новая категория").fill(categoryTitle);
  await categories.getByRole("button", { name: "Создать" }).click();
  const services = page.locator(".card").filter({ has: page.getByRole("heading", { name: "Услуги" }) });
  await services.getByLabel("Новая услуга").fill(serviceTitle);
  await services.getByLabel("Категория").selectOption({ label: categoryTitle });
  await services.getByRole("button", { name: "Создать" }).click();

  await page.goto("/admin/service-desk/templates");
  await expect(page.getByRole("heading", { name: "Шаблоны форм" })).toBeVisible();
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  await page.getByRole("button", { name: "Новая версия" }).click();
  await expect(page.getByText("Черновик можно изменять")).toBeVisible();
  await page.getByLabel("Тема по умолчанию").fill(`Request ${suffix}`);
  await page.getByLabel("Подсказка формы").fill("Browser QA help text");
  await page.getByRole("button", { name: "Сохранить настройки" }).click();
  const editor = page.locator(".card").filter({ has: page.getByRole("heading", { name: "Добавить поле" }) });
  await editor.getByLabel("Ключ").fill(`contact_email_${suffix}`);
  await editor.getByLabel("Название").fill(fieldLabel);
  await editor.getByLabel("Тип поля").selectOption("email");
  await editor.getByText("Обязательное поле").click();
  await editor.getByRole("button", { name: "Сохранить", exact: true }).click();
  await expect(page.getByText(fieldLabel)).toBeVisible();
  await page.getByRole("button", { name: "Предпросмотр" }).click();
  await expect(page.getByRole("heading", { name: "Предпросмотр формы" })).toBeVisible();
  await expect(page.getByLabel(fieldLabel)).toBeVisible();
  await attachScreenshot(page, testInfo, "template-preview");
  await page.getByRole("button", { name: "Опубликовать" }).click();
  await expect(page.getByText("Опубликованная версия доступна только для просмотра")).toBeVisible();
  await page.reload();
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  await expect(page.getByRole("button", { name: /Версия 1 · Опубликовано/ })).toBeVisible();
  diagnostics.assertClean();
});
