import { expect, test } from "@playwright/test";

import { attachScreenshot, expectNoHorizontalOverflow, loginAs, watchPage } from "./helpers";

test("selector keeps both anonymous module choices and next redirects", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  await page.goto("/");
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "Выберите сервис" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Проектный модуль/ })).toHaveAttribute(
    "href",
    "/login?next=%2Fprojects"
  );
  const serviceDeskCard = page.locator(".module-selector-card").filter({ hasText: "Service Desk" });
  await expect(serviceDeskCard).toHaveAttribute(
    "href",
    "/login?next=%2Fservice-desk"
  );
  await attachScreenshot(page, testInfo, "selector-desktop");

  await serviceDeskCard.click();
  await loginAs(page, "Менеджер Service Desk", "/service-desk");
  await expect(page.getByRole("heading", { name: "Каталог Service Desk" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Каталог Service Desk" })).toBeVisible();
  await page.getByRole("button", { name: "Выйти" }).click();
  await expect.poll(() => page.evaluate(() => localStorage.getItem("shpiu_project_showcase_token"))).toBeNull();
  diagnostics.assertClean();
});

test("selector and login are usable at 390x844", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Выберите сервис" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await attachScreenshot(page, testInfo, "selector-mobile");
  await page.getByRole("link", { name: /Проектный модуль/ }).click();
  await expect(page.getByRole("heading", { name: "Вход в PROM" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await attachScreenshot(page, testInfo, "login-mobile");
});
