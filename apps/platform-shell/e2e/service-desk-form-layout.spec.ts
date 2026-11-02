import { expect, test } from "@playwright/test";

import { expectNoHorizontalOverflow, loginAs, watchPage } from "./helpers";

test("SLA form fields stay aligned and fit the viewport", async ({ page }) => {
  const diagnostics = watchPage(page);

  await page.setViewportSize({ width: 1280, height: 720 });
  await loginAs(page, "Администратор Service Desk", "/admin/service-desk/sla");
  const calendarSection = page.locator(
    'section[aria-labelledby="sla-calendars-title"]',
  );
  const calendarForm = calendarSection.locator("form");
  const calendarName = calendarForm.getByLabel("Название календаря");
  const timezone = calendarForm.getByLabel("Часовой пояс");
  await expect(calendarName).toBeVisible();
  await expect(timezone).toBeVisible();

  const [nameBox, timezoneBox] = await Promise.all([
    calendarName.boundingBox(),
    timezone.boundingBox(),
  ]);
  expect(nameBox).not.toBeNull();
  expect(timezoneBox).not.toBeNull();
  expect(Math.abs(nameBox!.y - timezoneBox!.y)).toBeLessThanOrEqual(1);
  expect(Math.abs(nameBox!.height - timezoneBox!.height)).toBeLessThanOrEqual(
    1,
  );
  await expectNoHorizontalOverflow(page);

  await calendarForm
    .getByRole("button", { name: "Интервал", exact: true })
    .click();
  await expect(
    calendarForm.locator(".service-desk-sla-interval-row"),
  ).toHaveCount(2);
  await expectNoHorizontalOverflow(page);

  await page.setViewportSize({ width: 390, height: 844 });
  const header = page.getByRole("banner");
  const serviceSwitcher = header.getByRole("button", {
    name: "Сервисы: Service Desk",
  });
  const navigation = page.locator("#header-navigation");
  const headerTools = header.locator(".header-tools");
  const menuToggle = header.getByRole("button", {
    name: "Открыть меню",
    exact: true,
  });
  await expect(serviceSwitcher).toBeVisible();
  await expect(menuToggle).toHaveAttribute("aria-expanded", "false");
  await expect(navigation).toBeHidden();
  await expect(headerTools).toBeHidden();

  const [brandBox, switcherBox, headerActionsBox, menuBox] = await Promise.all([
    header.locator(".brand").boundingBox(),
    serviceSwitcher.boundingBox(),
    header.locator(".header-auth-actions").boundingBox(),
    menuToggle.boundingBox(),
  ]);
  expect(brandBox).not.toBeNull();
  expect(switcherBox).not.toBeNull();
  expect(headerActionsBox).not.toBeNull();
  expect(menuBox).not.toBeNull();
  expect(brandBox!.x + brandBox!.width).toBeLessThanOrEqual(switcherBox!.x + 1);
  expect(switcherBox!.x + switcherBox!.width).toBeLessThanOrEqual(
    headerActionsBox!.x + 1,
  );
  expect(headerActionsBox!.x + headerActionsBox!.width).toBeLessThanOrEqual(
    menuBox!.x + 1,
  );
  await expectNoHorizontalOverflow(page);

  await menuToggle.click();
  await expect(
    header.getByRole("button", { name: "Закрыть меню", exact: true }),
  ).toHaveAttribute("aria-expanded", "true");
  await expect(navigation).toBeVisible();
  await expect(headerTools).toBeVisible();
  const [navigationBox, headerToolsBox] = await Promise.all([
    navigation.boundingBox(),
    headerTools.boundingBox(),
  ]);
  expect(navigationBox).not.toBeNull();
  expect(headerToolsBox).not.toBeNull();
  expect(navigationBox!.y).toBeGreaterThanOrEqual(
    menuBox!.y + menuBox!.height - 1,
  );
  expect(headerToolsBox!.y).toBeGreaterThanOrEqual(
    navigationBox!.y + navigationBox!.height - 1,
  );
  await expectNoHorizontalOverflow(page);
  await header
    .getByRole("button", { name: "Закрыть меню", exact: true })
    .click();
  await expect(navigation).toBeHidden();

  await serviceSwitcher.click();
  const services = header.getByRole("navigation", {
    name: "Сервисы",
    exact: true,
  });
  await expect(services).toBeVisible();
  await expectNoHorizontalOverflow(page);
  await page.keyboard.press("Escape");
  await expect(services).toBeHidden();
  await expect(serviceSwitcher).toBeFocused();
  await serviceSwitcher.click();
  await services.getByRole("link", { name: "Проекты", exact: true }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await expect(
    page.getByRole("heading", { name: "Витрина проектов" }),
  ).toBeVisible();
  await expect(services).toBeHidden();
  await expectNoHorizontalOverflow(page);
  diagnostics.assertClean();
});
