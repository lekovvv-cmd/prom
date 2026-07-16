import { expect, test } from "@playwright/test";

import { attachScreenshot, expectNoHorizontalOverflow, loginAs, watchPage } from "./helpers";

test("SLA admin page contract works on desktop and mobile", async ({ page }, testInfo) => {
  const diagnostics = watchPage(page);
  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/sla");
  await expect(page.getByRole("heading", { name: "Настройка SLA" })).toBeVisible();
  for (const heading of ["Рабочее время", "Сроки SLA", "Где применять SLA", "Уведомления о риске"]) {
    await expect(page.getByRole("heading", { level: 2, name: heading, exact: true })).toBeVisible();
  }
  await attachScreenshot(page, testInfo, "sla-desktop");
  await page.setViewportSize({ width: 390, height: 844 });
  await page.reload();
  await expect(page.getByRole("heading", { name: "Настройка SLA" })).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await attachScreenshot(page, testInfo, "sla-mobile");
  diagnostics.assertClean();
});
