import { expect, test } from "@playwright/test";

import { attachScreenshot, createCatalogFixtureCleaner, loginAs, watchPage } from "./helpers";

const catalogFixtures = createCatalogFixtureCleaner();

test.afterEach(async ({ page }) => {
  await catalogFixtures.cleanup(page);
});

test("template preview keeps controls aligned within each row", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);

  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/templates");
  await page.getByLabel("Услуга").selectOption({ label: "Транспортное обслуживание" });
  await page.getByRole("button", { name: "Открыть предпросмотр" }).click();

  const preview = page.locator(".template-preview-card");
  await expect(preview).toBeVisible();
  const [eventName, peopleCount, studentsCount, startsAt] = await Promise.all([
    preview.getByLabel("Название мероприятия").boundingBox(),
    preview.getByLabel("Количество человек (всего)").boundingBox(),
    preview.getByLabel("Количество студентов").boundingBox(),
    preview.getByLabel("Дата и время начала мероприятия").boundingBox()
  ]);

  expect(eventName).not.toBeNull();
  expect(peopleCount).not.toBeNull();
  expect(studentsCount).not.toBeNull();
  expect(startsAt).not.toBeNull();
  expect(eventName!.y).toBe(peopleCount!.y);
  expect(studentsCount!.y).toBe(startsAt!.y);

  await attachScreenshot(page, testInfo, "template-preview-aligned");
  diagnostics.assertClean();
});

test("admin creates and publishes a template with production preview", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  const suffix = Date.now();
  const categoryTitle = `Template QA category ${suffix}`;
  const serviceTitle = `Template QA service ${suffix}`;
  const fieldLabel = `Contact email ${suffix}`;

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
  await expect(page.getByRole("heading", { name: "Шаблоны форм" })).toBeVisible();
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  await page.getByRole("button", { name: "Создать новую версию" }).click();
  await expect(page.getByText("Настройте поля, затем опубликуйте версию.")).toBeVisible();
  await page.getByLabel("Тема заявки по умолчанию").fill(`Request ${suffix}`);
  await page.getByLabel("Подсказка в начале формы").fill("Browser QA help text");
  await page.getByRole("button", { name: "Сохранить настройки формы" }).click();
  const editor = page.locator(".template-field-editor");
  await expect(editor.getByText("Системное имя", { exact: false })).toHaveCount(0);
  await editor.getByLabel("Название поля для пользователя").fill(fieldLabel);
  await expect(editor.getByText(`contact_email_${suffix}`, { exact: true })).toHaveCount(0);
  await editor.getByLabel("Тип ответа").selectOption("email");
  await editor.getByText("Это поле обязательно всегда").click();
  await editor.getByRole("button", { name: "Сохранить поле" }).click();
  await expect(page.getByText(fieldLabel)).toBeVisible();
  const dependentLabel = `Extra details ${suffix}`;
  await editor.getByLabel("Название поля для пользователя").fill(dependentLabel);
  await expect(editor.getByText(`extra_details_${suffix}`, { exact: true })).toHaveCount(0);
  await editor.getByText("Показывать это поле только при выполнении условия", { exact: true }).click();
  await editor.getByLabel("Поле для условия видимости 1").selectOption(`contact_email_${suffix}`);
  await editor.getByLabel("Значение для условия 1").fill("yes");
  await expect(editor.getByText("Поле не может ссылаться само на себя.")).toHaveCount(0);
  await editor.getByRole("button", { name: "Сохранить поле" }).click();
  await expect(page.getByText(dependentLabel)).toBeVisible();
  await page.getByRole("button", { name: "Открыть предпросмотр" }).click();
  await expect(page.getByRole("heading", { name: "Предпросмотр формы" })).toBeVisible();
  await expect(page.getByRole("textbox", { name: `${fieldLabel} *` })).toBeVisible();
  await attachScreenshot(page, testInfo, "template-preview");
  await page.getByRole("button", { name: "Опубликовать версию" }).click();
  await expect(page.getByText("Эта версия уже используется в заявках и доступна только для просмотра.")).toBeVisible();
  await page.reload();
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  const publishedVersion = page.getByLabel("Версии формы").getByRole("button", { name: "Версия 1" });
  await expect(publishedVersion).toBeVisible();
  await expect(publishedVersion).toContainText("Опубликована");
  diagnostics.assertClean();
});
