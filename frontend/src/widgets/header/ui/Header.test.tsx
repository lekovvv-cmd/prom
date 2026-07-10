import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../../app/providers/AppProviders", () => ({
  useAuth: () => ({
    canManageProjects: true,
    isAdmin: true,
    logout: vi.fn(),
    token: "token",
    user: { email: "admin@utmn.ru", role: "admin" }
  })
}));

vi.mock("../../../app/providers/ServiceDeskAccessProvider", () => ({
  useServiceDeskAccess: () => ({
    user: { id: "service-desk-admin" }
  })
}));

vi.mock("../../service-desk-notifications/ui/ServiceDeskNotificationCenter", () => ({
  ServiceDeskNotificationCenter: () => <span>notification-center-for-admin</span>
}));

vi.mock("../../service-desk-notifications/ui/ServiceDeskContextualCounters", () => ({
  ServiceDeskContextualCounters: () => <span>contextual-counters</span>
}));

import { Header } from "./Header";

describe("Header", () => {
  it("shows Service Desk notifications to a Projects admin with Service Desk access", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <Header />
      </MemoryRouter>
    );

    expect(html).toContain("notification-center-for-admin");
    expect(html).toContain("contextual-counters");
  });
});
