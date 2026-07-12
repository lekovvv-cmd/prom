import { expect, type Page, type TestInfo } from "@playwright/test";

export type DemoRole =
  | "Сотрудник"
  | "Руководитель проектов"
  | "Менеджер Service Desk"
  | "Администратор Service Desk"
  | "Администратор платформы";

export async function loginAs(page: Page, role: DemoRole, next: string) {
  await page.goto(`/login?next=${encodeURIComponent(next)}`);
  await page.getByRole("button").filter({ hasText: role }).click();
  await page.getByRole("button", { name: /^Войти$/ }).click();
  await expect(page).toHaveURL(new RegExp(`${next.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?:[?#]|$)`));
}

export function watchPage(page: Page) {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const failedResponses: string[] = [];

  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400) {
      failedResponses.push(`${response.status()} ${response.request().method()} ${response.url()}`);
    }
  });

  return {
    assertClean(
      allowedResponse?: (value: string) => boolean,
      allowedConsole?: (value: string) => boolean
    ) {
      expect(
        consoleErrors.filter((value) => !allowedConsole?.(value)),
        "unexpected browser console errors"
      ).toEqual([]);
      expect(pageErrors, "unexpected uncaught page errors").toEqual([]);
      expect(
        failedResponses.filter((value) => !allowedResponse?.(value)),
        "unexpected failed network responses"
      ).toEqual([]);
    }
  };
}

export async function attachScreenshot(page: Page, testInfo: TestInfo, name: string) {
  await testInfo.attach(name, {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png"
  });
}

export async function expectNoHorizontalOverflow(page: Page) {
  const dimensions = await page.evaluate(() => ({
    viewport: window.innerWidth,
    content: document.documentElement.scrollWidth
  }));
  expect(dimensions.content, `horizontal overflow: ${JSON.stringify(dimensions)}`).toBeLessThanOrEqual(
    dimensions.viewport + 1
  );
}
