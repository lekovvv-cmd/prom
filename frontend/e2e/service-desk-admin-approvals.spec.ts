import { expect, test } from "@playwright/test";

import { loginAs, watchPage } from "./helpers";

test("approval editor configures, edits and removes a workflow stage through UI", async ({ page }) => {
  const diagnostics = watchPage(page);
  const suffix = Date.now();
  const categoryTitle = `Approval QA category ${suffix}`;
  const serviceTitle = `Approval QA service ${suffix}`;
  const stageTitle = `Approval QA stage ${suffix}`;
  const editedStageTitle = `${stageTitle} edited`;

  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/catalog");
  const categories = page.locator(".card").filter({ has: page.getByRole("heading", { name: "Категории" }) });
  await categories.getByLabel("Новая категория").fill(categoryTitle);
  await categories.getByRole("button", { name: "Создать" }).click();
  const services = page.locator(".card").filter({ has: page.getByRole("heading", { name: "Услуги" }) });
  await services.getByLabel("Новая услуга").fill(serviceTitle);
  await services.getByLabel("Категория").selectOption({ label: categoryTitle });
  await services.getByRole("button", { name: "Создать" }).click();

  await page.goto("/admin/service-desk/templates");
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  await page.getByRole("button", { name: "Новая версия" }).click();

  await page.goto("/admin/service-desk/approvals");
  await expect(page.getByRole("heading", { name: "Согласования" })).toBeVisible();
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  await page.getByLabel("Версия формы").selectOption({ index: 1 });
  await expect(page.getByText("Без согласования")).toBeVisible();
  await page.getByRole("button", { name: "Включить процесс по этапам" }).click();
  await page.getByLabel("Название нового этапа").fill(stageTitle);
  await page.getByLabel("Правило нового этапа").selectOption("any");
  await page.getByRole("button", { name: "Добавить этап" }).click();
  let stageRow = page.locator(".admin-config-row").filter({ hasText: stageTitle });
  await expect(stageRow).toContainText("Достаточно одного");
  await stageRow.getByLabel("Согласующий").selectOption({ index: 1 });
  await stageRow.locator("button").last().click();
  await expect(stageRow).toContainText("1 согласующих");
  await stageRow.getByRole("button", { name: "Изменить" }).click();
  stageRow = page.locator(".admin-config-row").filter({ has: page.getByLabel("Название этапа") });
  await stageRow.getByLabel("Название этапа").fill(editedStageTitle);
  await stageRow.getByRole("button", { name: "Сохранить" }).click();
  stageRow = page.locator(".admin-config-row").filter({ hasText: editedStageTitle });
  await expect(stageRow).toBeVisible();
  await stageRow.getByRole("button", { name: "Удалить", exact: true }).click();
  await expect(page.getByText(editedStageTitle)).toHaveCount(0);
  await page.getByRole("button", { name: "Отключить процесс" }).click();
  await expect(page.getByText("Без согласования")).toBeVisible();
  await page.reload();
  await page.getByLabel("Услуга").selectOption({ label: serviceTitle });
  await page.getByLabel("Версия формы").selectOption({ index: 1 });
  await expect(page.getByText("Без согласования")).toBeVisible();
  diagnostics.assertClean();
});
