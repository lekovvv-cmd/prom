import { expect, test } from "@playwright/test";

import { attachScreenshot, loginAs, watchPage } from "./helpers";

test("invalid seeded form focuses first error and sends no ticket mutation", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  await loginAs(page, "Менеджер Service Desk", "/service-desk");
  await page.getByPlaceholder("Например, доступ к системе").fill("Заказ воды");
  await page.locator(".service-desk-service-card").filter({ hasText: "Заказ воды" })
    .getByRole("link", { name: "Открыть услугу" }).click();

  let mutations = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().includes("/tickets")) mutations += 1;
  });
  await page.getByLabel("Тема заявки").fill("");
  await page.getByLabel("Описание").fill("");
  await page.getByRole("button", { name: "Отправить заявку" }).click();
  await expect(page.getByText("Заполните обязательные поля")).toBeVisible();
  await expect(page.getByLabel("Тема заявки")).toBeFocused();
  expect(mutations).toBe(0);
  await attachScreenshot(page, testInfo, "ticket-validation");
  diagnostics.assertClean();
});
