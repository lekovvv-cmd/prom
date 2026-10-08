import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers";

test("a long response form survives bearer expiry and submits with one renewal", async ({
  page,
  request,
}) => {
  const title = `E2E renewal ${Date.now()}`;
  await loginAs(page, "Администратор платформы", "/projects");
  const adminToken = await page.evaluate(async () => {
    const response = await fetch("/api/access/v1/session/token", {
      credentials: "include",
    });
    return ((await response.json()) as { access_token: string }).access_token;
  });
  const headers = { Authorization: `Bearer ${adminToken}` };
  const created = await request.post("/api/projects/v1/admin/projects", {
    headers,
    data: {
      title,
      short_description: "Проверка долгой формы отклика",
      description: "Проверка сохранения введённых данных при продлении токена",
      goal: "Проверить продление токена",
      status: "active",
    },
  });
  expect(created.status(), await created.text()).toBe(201);
  const projectId = ((await created.json()) as { id: string }).id;

  try {
    await page.getByRole("button", { name: "Выйти" }).click();
    await loginAs(page, "Сотрудник", `/projects/${projectId}`);
    await expect(
      page.getByRole("heading", { name: "Откликнуться на проект" }),
    ).toBeVisible();

    const comment = "Данные длинной формы должны сохраниться до отправки";
    await page.getByLabel("Комментарий").fill(comment);
    await page.locator('#response-form input[type="file"]').setInputFiles({
      name: "renewal.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("file survives bearer renewal"),
    });

    let renewals = 0;
    let attempts = 0;
    let reloads = 0;
    page.on("load", () => {
      reloads += 1;
    });
    await page.route("**/api/access/v1/session/token", async (route) => {
      renewals += 1;
      await new Promise((resolve) => setTimeout(resolve, 500));
      await route.continue();
    });
    await page.route(
      `**/api/projects/v1/projects/${projectId}/responses`,
      async (route) => {
        attempts += 1;
        if (attempts === 1) {
          await route.fulfill({
            status: 401,
            contentType: "application/problem+json",
            body: JSON.stringify({ detail: "Invalid token" }),
          });
        } else {
          await route.continue();
        }
      },
    );

    await page.getByRole("button", { name: "Отправить отклик" }).click();
    await expect.poll(() => renewals).toBe(1);
    await expect(page.getByLabel("Комментарий")).toHaveValue(comment);
    await expect(page.getByText("renewal.txt")).toBeVisible();
    await expect(page.getByText("Отклик отправлен")).toBeVisible();
    expect(attempts).toBe(2);
    expect(renewals).toBe(1);
    expect(reloads).toBe(0);
    await expect(page.getByText("Invalid token")).toHaveCount(0);
  } finally {
    await request.delete(`/api/projects/v1/admin/projects/${projectId}`, {
      headers,
    });
  }
});
