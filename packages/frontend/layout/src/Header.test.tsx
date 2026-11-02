import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("@prom/auth", () => ({
  useAuth: () => ({
    hasPermission: () => true,
    isAdmin: true,
    isAuthenticated: true,
    logout: vi.fn(),
    modules: [
      { id: "projects", permissions: [] },
      { id: "service-desk", permissions: [] },
    ],
    user: { email: "admin@utmn.ru", display_name: "Администратор" },
  }),
}));

import {
  Header,
  HeaderToolsProvider,
  ServiceNavigationProvider,
} from "./Header";

describe("Header", () => {
  it("derives the selected service from its registered route prefixes", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={["/admin/service-desk/access"]}>
        <ServiceNavigationProvider
          services={[
            {
              id: "projects",
              title: "Проекты",
              basePath: "/projects",
              routePrefixes: ["/projects", "/admin"],
            },
            {
              id: "service-desk",
              title: "Поддержка",
              basePath: "/service-desk",
              routePrefixes: ["/service-desk", "/admin/service-desk"],
            },
          ]}
        >
          <Header />
        </ServiceNavigationProvider>
      </MemoryRouter>,
    );
    expect(html).toContain('aria-label="Сервисы: Поддержка"');
    expect(html).not.toContain('class="module-switcher"');
  });

  it("does not select a registered service without module access", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={["/library"]}>
        <ServiceNavigationProvider
          services={[
            {
              id: "library",
              title: "Библиотека",
              basePath: "/library",
              routePrefixes: ["/library"],
            },
          ]}
        >
          <Header />
        </ServiceNavigationProvider>
      </MemoryRouter>,
    );
    expect(html).toContain('aria-label="Сервисы: Все сервисы"');
    expect(html).not.toContain("Библиотека");
  });

  it("shows Service Desk notifications to a Projects admin with Service Desk access", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter initialEntries={["/projects"]}>
        <HeaderToolsProvider tools={<span>notification-center-for-admin</span>}>
          <Header />
        </HeaderToolsProvider>
      </MemoryRouter>,
    );

    expect(html).toContain('aria-label="Профиль: admin@utmn.ru"');
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
