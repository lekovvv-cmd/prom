import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("@prom/auth", () => ({
  useAuth: () => ({
    canManageProjects: true,
    isAdmin: true,
    isAuthenticated: true,
    logout: vi.fn(),
    modules: [
      { id: "projects", permissions: [] },
      { id: "service-desk", permissions: [] },
    ],
    user: { email: "admin@utmn.ru", role: "platform_admin" },
  }),
}));

import { Header, HeaderToolsProvider } from "./Header";

describe("Header", () => {
  it("shows Service Desk notifications to a Projects admin with Service Desk access", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={["/projects"]}>
        <HeaderToolsProvider tools={<span>notification-center-for-admin</span>}>
          <Header />
        </HeaderToolsProvider>
      </MemoryRouter>,
    );

    expect(html).toContain("notification-center-for-admin");
    expect(html).not.toContain("contextual-counters");
  });

  it("shows only the UTMN brand outside product modules", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={["/"]}>
        <Header />
      </MemoryRouter>,
    );

    expect(html).toContain('alt="UTMN"');
    expect(html).not.toContain("ШПИУ Проекты");
    expect(html).not.toContain("ШПИУ Service Desk");
    expect(html).not.toContain("notification-center-for-admin");
  });
});
