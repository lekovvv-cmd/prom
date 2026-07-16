import { describe, expect, it } from "vitest";

import type { ServiceDeskTicket } from "../model/types";
import { findCurrentUserApproval, getTicketActionAvailability } from "./ticketActions";

describe("Service Desk ticket actions", () => {
  it("maps only backend allowed_actions to approval controls", () => {
    expect(getTicketActionAvailability(["approve", "reject"])).toEqual({
      canApprove: true,
      canReject: true
    });
    expect(getTicketActionAvailability([])).toEqual({
      canApprove: false,
      canReject: false
    });
  });

  it("selects only the current user's pending approval in an active stage", () => {
    const ticket = {
      approval_stages: [
        {
          status: "pending",
          started_at: "2026-07-10T10:00:00Z",
          approvals: [
            { id: "approval-1", approver_user_id: "user-1", status: "pending" },
            { id: "approval-2", approver_user_id: "user-2", status: "approved" }
          ]
        },
        {
          status: "pending",
          started_at: null,
          approvals: [{ id: "approval-3", approver_user_id: "user-1", status: "pending" }]
        }
      ]
    } as ServiceDeskTicket;

    expect(findCurrentUserApproval(ticket, "user-1")?.id).toBe("approval-1");
    expect(findCurrentUserApproval(ticket, "user-2")).toBeNull();
  });
});
