import { expect, test } from "@playwright/test";

import { attachScreenshot, expectNoHorizontalOverflow, loginAs, watchPage } from "./helpers";

test("dictionaries support create, values, duplicate validation and activation through UI", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  const suffix = Date.now();
  const title = `QA dictionary ${suffix}`;
  const value = `qa_${suffix}`;

  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/dictionaries");
  await expect(page.getByRole("heading", { name: "Справочники" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Создать" })).toBeDisabled();
  await page.getByLabel("Код").fill(`qa_dictionary_${suffix}`);
  await page.getByLabel("Название").fill(title);
  await page.getByRole("button", { name: "Создать" }).click();
  await page.getByLabel("Подпись").fill("Первое значение");
  await page.getByLabel("Значение").fill(value);
  await page.getByRole("button", { name: "Добавить значение" }).click();
  const itemRow = page.locator(".admin-config-row").filter({ hasText: `Первое значение · ${value}` });
  await expect(itemRow).toBeVisible();

  await page.getByLabel("Подпись").fill("Дубликат");
  await page.getByLabel("Значение").fill(value);
  await page.getByRole("button", { name: "Добавить значение" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await itemRow.getByRole("button", { name: "Выключить" }).click();
  await expect(itemRow.getByRole("button", { name: "Включить" })).toBeVisible();
  await itemRow.getByRole("button", { name: "Включить" }).click();
  await page.getByRole("button", { name: "Выключить справочник" }).click();
  await expect(page.getByRole("button", { name: "Включить справочник" })).toBeVisible();
  await page.getByRole("button", { name: "Включить справочник" }).click();
  await page.reload();
  await page.getByRole("button", { name: title }).click();
  await expect(page.getByText(`Первое значение · ${value}`)).toBeVisible();
  await attachScreenshot(page, testInfo, "dictionary-admin");
  diagnostics.assertClean(
    (response) => response.startsWith("409 POST") && response.includes("/admin/dictionaries/"),
    (message) => message.includes("409")
  );
});

test("routing rule supports validation, create, edit, reload and delete through UI", async ({ page }) => {
  const diagnostics = watchPage(page);
  const suffix = Date.now();
  const name = `QA routing ${suffix}`;
  const editedName = `${name} edited`;

  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/routing");
  await expect(page.getByRole("heading", { name: "Маршрутизация Service Desk" })).toBeVisible();
  await page.getByRole("button", { name: "Сохранить правило" }).click();
  await expect(page.getByLabel("Название")).toBeFocused();
  await page.getByLabel("Название").fill(name);
  await page.getByRole("button", { name: "Добавить" }).click();
  await page.getByLabel("Поле условия 1").selectOption("priority");
  await page.getByLabel("Значение условия 1").selectOption("high");
  await page.getByLabel("Тип действия").selectOption("set_priority");
  await page.getByLabel("Новый приоритет").selectOption("critical");
  await page.getByRole("button", { name: "Сохранить правило" }).click();
  let card = page.locator(".service-desk-routing-rule-card").filter({ hasText: name });
  await expect(card).toContainText("Приоритет заявки: high");
  await expect(card).toContainText("Установить приоритет: Критический");
  await card.getByRole("button", { name: "Редактировать" }).click();
  await page.getByLabel("Название").fill(editedName);
  await page.getByText("Правило активно").click();
  await page.getByRole("button", { name: "Сохранить правило" }).click();
  card = page.locator(".service-desk-routing-rule-card").filter({ hasText: editedName });
  await expect(card).toContainText("Выключено");
  await page.reload();
  card = page.locator(".service-desk-routing-rule-card").filter({ hasText: editedName });
  await expect(card).toContainText("Выключено");
  page.once("dialog", (dialog) => dialog.accept());
  await card.getByRole("button", { name: "Удалить" }).click();
  await expect(card).toHaveCount(0);
  diagnostics.assertClean();
});

test("remaining admin sections satisfy direct-link page contract on desktop and mobile", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  await loginAs(page, "Администратор Service Desk", "/admin/service-desk");
  for (const [path, expectedUrl, heading] of [
    ["/admin/service-desk", /\/admin\/service-desk$/, "Service Desk - обзор"],
    ["/admin/service-desk/tickets", /\/admin\/service-desk\/tickets$/, "Рабочее место Service Desk"],
    ["/admin/service-desk/calendars", /\/admin\/service-desk\/sla\?section=calendars$/, "SLA Service Desk"]
  ] as const) {
    await page.goto(path);
    await expect(page).toHaveURL(expectedUrl);
    await expect(page.getByRole("heading", { level: 1, name: heading })).toBeVisible();
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expectNoHorizontalOverflow(page);
  await attachScreenshot(page, testInfo, "admin-mobile");
  diagnostics.assertClean();
});
