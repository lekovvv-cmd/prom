import { expect, test } from "@playwright/test";

test.skip(
  process.env.E2E_PILOT !== "true",
  "Pilot selector is available in the pilot build only",
);

const user = {
  id: "pilot-admin",
  external_subject: "pilot:pilot.admin01@utmn.ru",
  email: "pilot.admin01@utmn.ru",
  display_name: "Администратор PROM 1",
  department: "ТюмГУ",
  position: "Администратор",
  is_active: true,
  session_version: 1,
};

const session = {
  user,
  modules: [{ id: "projects", permissions: ["projects.access"] }],
  permissions: ["platform.admin", "projects.access"],
};

test("pilot account double click creates one request and redirects once", async ({
  page,
}) => {
  let loginRequests = 0;
  await page.route("**/api/access/v1/session", (route) =>
    route.fulfill({ status: 401, body: "{}" }),
  );
  await page.route("**/api/access/v1/auth/pilot/login", async (route) => {
    loginRequests += 1;
    await new Promise((resolve) => setTimeout(resolve, 150));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(session),
    });
  });
  await page.route("**/api/access/v1/session/token", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "test-token",
        token_type: "Bearer",
        session,
      }),
    }),
  );

  await page.goto("/login");
  await page
    .getByRole("button", { name: "Администратор 1" })
    .evaluate((element) => {
      element.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      element.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
  await expect(page).toHaveURL(/\/projects(?:[?#]|$)/);
  expect(loginRequests).toBe(1);
});

test("pilot login shows an error and allows retry without reloading", async ({
  page,
}) => {
  let loginRequests = 0;
  await page.route("**/api/access/v1/session", (route) =>
    route.fulfill({ status: 401, body: "{}" }),
  );
  await page.route("**/api/access/v1/auth/pilot/login", async (route) => {
    loginRequests += 1;
    if (loginRequests === 1) {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Попробуйте ещё раз" }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(session),
    });
  });
  await page.route("**/api/access/v1/session/token", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "test-token",
        token_type: "Bearer",
        session,
      }),
    }),
  );

  await page.goto("/login");
  const selected = page.getByRole("button", { name: "Администратор 1" });
  await selected.click();
  await expect(page.getByRole("alert")).toBeVisible();
  expect(page.url()).toContain("/login");
  await selected.click();
  await expect(page).toHaveURL(/\/projects(?:[?#]|$)/);
  expect(loginRequests).toBe(2);
});
