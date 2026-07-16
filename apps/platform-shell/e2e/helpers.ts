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

type CatalogFixture = {
  categoryTitles?: string[];
  serviceTitles?: string[];
};

type TrackedCatalogFixture = CatalogFixture & {
  token: string;
};

/**
 * E2E scenarios create catalog data through the same UI and API as a real
 * administrator. Deactivate only the explicitly registered fixtures after the
 * test, so the public catalog never accumulates QA services or categories.
 */
export function createCatalogFixtureCleaner() {
  const fixtures: TrackedCatalogFixture[] = [];

  return {
    async track(page: Page, fixture: CatalogFixture) {
      const token = await page.evaluate(() => localStorage.getItem("shpiu_project_showcase_token"));
      if (!token) throw new Error("Невозможно очистить E2E-фикстуру: отсутствует авторизованная сессия.");
      fixtures.push({ ...fixture, token });
    },

    trackWithToken(token: string, fixture: CatalogFixture) {
      fixtures.push({ ...fixture, token });
    },

    async cleanup(page: Page) {
      const tracked = fixtures.splice(0);
      if (!tracked.length) return;

      const failures = await page.evaluate(async (items) => {
        const errors: string[] = [];

        for (const item of items) {
          const headers = { Authorization: `Bearer ${item.token}` };
          const deactivateByTitle = async (kind: "services" | "categories", title: string) => {
            const listed = await fetch(`/service-desk-api/admin/${kind}?q=${encodeURIComponent(title)}`, { headers });
            if (!listed.ok) {
              errors.push(`Не удалось найти ${kind} «${title}»: ${listed.status}`);
              return;
            }

            const entries = await listed.json() as Array<{ id: string; title: string; deleted_at: string | null }>;
            const matching = entries.filter((entry) => entry.title === title && entry.deleted_at === null);
            for (const entry of matching) {
              const response = await fetch(`/service-desk-api/admin/${kind}/${entry.id}/deactivate`, {
                method: "POST",
                headers
              });
              if (!response.ok) errors.push(`Не удалось отключить ${kind} «${title}»: ${response.status}`);
            }
          };

          for (const title of item.serviceTitles ?? []) await deactivateByTitle("services", title);
          for (const title of item.categoryTitles ?? []) await deactivateByTitle("categories", title);
        }

        return errors;
      }, tracked);

      if (failures.length) throw new Error(`Не удалось очистить E2E-фикстуры каталога:\n${failures.join("\n")}`);
    }
  };
}
