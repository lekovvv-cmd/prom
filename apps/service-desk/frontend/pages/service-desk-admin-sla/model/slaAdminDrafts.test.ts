import { describe, expect, it } from "vitest";

import {
  bindingDraftToPayload,
  calendarDraftToPayload,
  escalationDraftToPayload,
  policyDraftToPayload,
} from "./slaAdminDrafts";

describe("SLA admin payload builders", () => {
  it("keeps arbitrary business hours and multiple custom-hour intervals", () => {
    const payload = calendarDraftToPayload({
      name: " Weekend support ",
      timezone: "Asia/Yekaterinburg",
      isActive: true,
      businessHours: [
        { weekday: 5, start_time: "10:00", end_time: "13:00" },
        { weekday: 5, start_time: "14:00", end_time: "16:00" },
      ],
      exceptions: [
        { date: "2026-08-01", type: "holiday", description: " Holiday " },
        {
          date: "2026-08-02",
          type: "custom_hours",
          start_time: "09:00",
          end_time: "12:00",
        },
        {
          date: "2026-08-02",
          type: "custom_hours",
          start_time: "13:00",
          end_time: "15:00",
        },
      ],
    });
    expect(payload.business_hours).toHaveLength(2);
    expect(payload.exceptions).toEqual([
      { date: "2026-08-01", type: "holiday", description: "Holiday" },
      {
        date: "2026-08-02",
        type: "custom_hours",
        start_time: "09:00",
        end_time: "12:00",
      },
      {
        date: "2026-08-02",
        type: "custom_hours",
        start_time: "13:00",
        end_time: "15:00",
      },
    ]);
  });

  it("builds editable policy and multi-condition field_value binding", () => {
    expect(
      policyDraftToPayload({
        name: " Priority SLA ",
        description: " Critical requests ",
        isActive: false,
        calendarId: "calendar-id",
        firstResponseMinutes: "15",
        resolutionMinutes: "180",
        pauseStatuses: ["waiting_requester"],
      }),
    ).toMatchObject({
      name: "Priority SLA",
      description: "Critical requests",
      is_active: false,
      pause_statuses: ["waiting_requester"],
    });
    expect(
      bindingDraftToPayload({
        name: " Critical impact ",
        policyId: "policy-id",
        priority: "20",
        isActive: true,
        conditions: [
          { field: "priority", value: "high" },
          { field: "field_value", field_key: " impact ", value: " critical " },
        ],
      }).conditions,
    ).toEqual([
      { field: "priority", value: "high" },
      { field: "field_value", field_key: "impact", value: "critical" },
    ]);
  });

  it("includes specific recipient and clears it for other recipient types", () => {
    const base = {
      policyId: "policy-id",
      metric: "resolution" as const,
      thresholdPercent: "73",
      actionType: "create_in_app_notification" as const,
      recipientType: "specific_user" as const,
      recipientUserId: "recipient-id",
      isActive: true,
    };
    expect(escalationDraftToPayload(base).recipient_user_id).toBe(
      "recipient-id",
    );
    expect(
      escalationDraftToPayload({ ...base, recipientType: "requester" })
        .recipient_user_id,
    ).toBeNull();
  });
});
