import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { NotificationList } from "./ServiceDeskNotificationCenter";

describe("NotificationList", () => {
  it("renders empty state", () => {
    const html = renderToStaticMarkup(<NotificationList notifications={[]} onRead={vi.fn()} />);
    expect(html).toContain("Уведомлений нет");
  });

  it("distinguishes unread and supports ticketless notifications", () => {
    const html = renderToStaticMarkup(<MemoryRouter><NotificationList onRead={vi.fn()} notifications={[
      { id: "1", recipient_user_id: "u", ticket_id: "ticket", event_type: "ticket_started", title: "В работе", body: "Начата работа", is_read: false, created_at: "2026-07-11T10:00:00Z", read_at: null },
      { id: "2", recipient_user_id: "u", ticket_id: null, event_type: "sla_warning", title: "Системное", body: "Без заявки", is_read: true, created_at: "2026-07-11T10:00:00Z", read_at: "2026-07-11T10:01:00Z" }
    ]} /></MemoryRouter>);
    expect(html).toContain("is-unread");
    expect(html).toContain("is-read");
    expect(html.match(/Открыть заявку/g)?.length).toBe(1);
    expect(html).toContain("/service-desk/tickets/ticket");
  });
});
