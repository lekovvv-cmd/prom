import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const serviceDeskUrl = process.env.E2E_SERVICE_DESK_URL ?? "http://127.0.0.1:8001";

async function loginAsManager(page: Page) {
  await page.goto("/login");
  await page.getByRole("button", { name: /Руководитель/ }).click();
  await page.getByRole("button", { name: /^Войти$/ }).click();
  await expect(page).toHaveURL(/\/projects$/);
  await expect(
    page.getByRole("banner").getByRole("link", { name: /manager@utmn\.ru/ })
  ).toBeVisible();
  const token = await page.evaluate(() => localStorage.getItem("shpiu_project_showcase_token"));
  expect(token).toBeTruthy();
  return token as string;
}

async function serviceDeskRequest<T>(
  request: APIRequestContext,
  token: string,
  method: "get" | "post" | "put",
  path: string,
  data?: unknown
) {
  const response = await request[method](`${serviceDeskUrl}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    data
  });
  expect(response.ok(), await response.text()).toBeTruthy();
  return (await response.json()) as T;
}

test("Service Desk flow: approver reviews and approves a ticket", async ({ page, request }) => {
  const token = await loginAsManager(page);
  const currentUser = await serviceDeskRequest<{ id: string }>(request, token, "get", "/me");
  const suffix = Date.now();

  const category = await serviceDeskRequest<{ id: string }>(
    request,
    token,
    "post",
    "/admin/categories",
    { title: `E2E approval category ${suffix}` }
  );
  const service = await serviceDeskRequest<{ id: string }>(
    request,
    token,
    "post",
    "/admin/services",
    { category_id: category.id, title: `E2E approval service ${suffix}` }
  );
  const version = await serviceDeskRequest<{ id: string }>(
    request,
    token,
    "post",
    `/admin/services/${service.id}/versions`
  );
  const configured = await serviceDeskRequest<{ workflow: { id: string } }>(
    request,
    token,
    "put",
    `/admin/template-versions/${version.id}/approval-workflow`,
    { approval_mode: "workflow", name: "E2E согласование" }
  );
  await serviceDeskRequest(
    request,
    token,
    "post",
    `/admin/approval-workflows/${configured.workflow.id}/stages`,
    { title: "Согласование руководителя", decision_rule: "any" }
  );
  const workflow = await serviceDeskRequest<{
    workflow: { stages: Array<{ id: string; title: string }> };
  }>(request, token, "get", `/admin/template-versions/${version.id}/approval-workflow`);
  const stageId = workflow.workflow.stages.find(
    (item) => item.title === "Согласование руководителя"
  )?.id;
  expect(stageId).toBeTruthy();
  await serviceDeskRequest(
    request,
    token,
    "post",
    `/admin/approval-stages/${stageId}/approvers`,
    { service_desk_user_id: currentUser.id }
  );
  await serviceDeskRequest(
    request,
    token,
    "post",
    `/admin/template-versions/${version.id}/publish`
  );

  const draft = await serviceDeskRequest<{ id: string }>(
    request,
    token,
    "post",
    "/tickets/drafts",
    {
      service_id: service.id,
      title: `E2E заявка ${suffix}`,
      description: "Проверка защищённого UI согласования."
    }
  );
  const ticket = await serviceDeskRequest<{ id: string; number: string }>(
    request,
    token,
    "post",
    `/tickets/${draft.id}/submit`
  );

  await page.goto(`/service-desk/tickets/${ticket.id}`);
  await expect(page.getByRole("heading", { level: 1, name: ticket.number })).toBeVisible();
  await expect(page.getByRole("heading", { name: `E2E заявка ${suffix}` })).toBeVisible();
  await expect(page.getByText("На согласовании")).toBeVisible();
  await expect(page.getByRole("button", { name: "Согласовать" })).toBeVisible();

  await page.getByRole("button", { name: "Уведомления Service Desk" }).click();
  const notificationCenter = page.getByRole("region", { name: "Центр уведомлений" });
  await expect(notificationCenter.getByText("Требуется согласование")).toBeVisible();
  await expect(notificationCenter.getByRole("link", { name: "Открыть заявку" }).first()).toHaveAttribute(
    "href", `/service-desk/tickets/${ticket.id}`
  );
  await notificationCenter.getByRole("button", { name: "Прочитать все" }).click();
  await expect(notificationCenter.getByText("Всё прочитано")).toBeVisible();

  await page.getByRole("button", { name: "Согласовать" }).click();
  const dialog = page.getByRole("dialog", { name: "Согласовать заявку" });
  await dialog.getByLabel("Комментарий").fill("E2E: согласовано");
  await dialog.getByRole("button", { name: "Подтвердить согласование" }).click();

  await expect(dialog).toBeHidden();
  await expect(page.getByText("Согласована")).toBeVisible();
  await expect(page.locator(".service-desk-approvals").getByText("E2E: согласовано")).toBeVisible();
  await expect(page.getByRole("button", { name: "Согласовать" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Отклонить" })).toHaveCount(0);
});

test("Service Desk SLA admin creates a business calendar", async ({ page, request }) => {
  const token = await loginAsManager(page);
  const suffix = Date.now();
  await page.goto("/service-desk/admin/sla");
  await expect(page.getByRole("heading", { name: "SLA Service Desk" })).toBeVisible();
  await page.getByLabel("Название").first().fill(`E2E SLA ${suffix}`);
  await page.getByRole("button", { name: /Создать календарь/ }).click();
  await expect(page.getByRole("strong").filter({ hasText: `E2E SLA ${suffix}` })).toBeVisible();
  const calendars = await serviceDeskRequest<Array<{ name: string }>>(
    request, token, "get", "/admin/sla/calendars"
  );
  expect(calendars.some((item) => item.name === `E2E SLA ${suffix}`)).toBeTruthy();
});
