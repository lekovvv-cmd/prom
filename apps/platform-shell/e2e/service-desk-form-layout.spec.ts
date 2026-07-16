import { expect, test } from "@playwright/test";

import { expectNoHorizontalOverflow, loginAs, watchPage } from "./helpers";

test("SLA form fields stay aligned and fit the viewport", async ({ page }) => {
  const diagnostics = watchPage(page);

  await page.setViewportSize({ width: 1280, height: 720 });
  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/sla");
  const calendarSection = page.locator('section[aria-labelledby="sla-calendars-title"]');
  const calendarForm = calendarSection.locator("form");
  const calendarName = calendarForm.getByLabel("Название календаря");
  const timezone = calendarForm.getByLabel("Часовой пояс");
  await expect(calendarName).toBeVisible();
  await expect(timezone).toBeVisible();

  const [nameBox, timezoneBox] = await Promise.all([calendarName.boundingBox(), timezone.boundingBox()]);
  expect(nameBox).not.toBeNull();
  expect(timezoneBox).not.toBeNull();
  expect(Math.abs(nameBox!.y - timezoneBox!.y)).toBeLessThanOrEqual(1);
  expect(Math.abs(nameBox!.height - timezoneBox!.height)).toBeLessThanOrEqual(1);
  await expectNoHorizontalOverflow(page);

  await calendarForm.getByRole("button", { name: "Интервал", exact: true }).click();
  await expect(calendarForm.locator(".service-desk-sla-interval-row")).toHaveCount(2);
  await expectNoHorizontalOverflow(page);

  await page.setViewportSize({ width: 390, height: 844 });
  const [brandBox, headerActionsBox, moduleSwitcherBox, navigationBox, statusBox] = await Promise.all([
    page.locator(".brand").boundingBox(),
    page.locator(".header-auth-actions").boundingBox(),
    page.locator(".module-switcher").boundingBox(),
    page.locator(".main-nav").boundingBox(),
    page.locator(".service-desk-header-status").boundingBox()
  ]);
  expect(brandBox).not.toBeNull();
  expect(headerActionsBox).not.toBeNull();
  expect(moduleSwitcherBox).not.toBeNull();
  expect(navigationBox).not.toBeNull();
  expect(statusBox).not.toBeNull();
  expect(brandBox!.x + brandBox!.width).toBeLessThanOrEqual(headerActionsBox!.x + 1);
  expect(moduleSwitcherBox!.y).toBeGreaterThanOrEqual(brandBox!.y + brandBox!.height - 1);
  expect(navigationBox!.y).toBeGreaterThanOrEqual(moduleSwitcherBox!.y + moduleSwitcherBox!.height - 1);
  expect(statusBox!.y).toBeGreaterThanOrEqual(navigationBox!.y + navigationBox!.height - 1);
  await expectNoHorizontalOverflow(page);
  diagnostics.assertClean();
});
