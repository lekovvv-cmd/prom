import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ServiceDeskWorkbenchTable } from "./ServiceDeskWorkbenchTable";

describe("ServiceDeskWorkbenchTable", () => {
  it("renders only server-provided actions and display names", () => {
    const html = renderToStaticMarkup(
      <MemoryRouter>
        <ServiceDeskWorkbenchTable
          onAction={() => undefined}
          items={[
            {
              ticket_id: "ticket",
              number: "SD-1",
              title: "Проверка",
              service: { id: "s", title: "Сеть" },
              category: { id: "c", title: "ИТ" },
              requester: { id: "r", display_name: "Заявитель" },
              assignee: null,
              priority: "high",
              status: "assigned",
              sla: {
                state: "on_track",
                metric: "first_response",
                due_at: null,
              },
              created_at: "2026-01-01T00:00:00Z",
              updated_at: "2026-01-01T00:00:00Z",
              allowed_actions: ["start"],
              active_approval_id: null,
            },
          ]}
        />
      </MemoryRouter>,
    );
    expect(html).toContain("Взять в работу");
    expect(html).not.toContain("Согласовать");
    expect(html).toContain("Заявитель");
    expect(html).toContain("/service-desk/tickets/ticket");
  });
});
