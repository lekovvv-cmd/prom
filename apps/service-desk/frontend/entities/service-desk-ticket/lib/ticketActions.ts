import type {
  ServiceDeskAllowedAction,
  ServiceDeskTicket,
  ServiceDeskTicketApproval,
} from "../model/types";

export function getTicketActionAvailability(
  allowedActions: ServiceDeskAllowedAction[],
) {
  const actions = new Set(allowedActions);
  return {
    canApprove: actions.has("approve"),
    canReject: actions.has("reject"),
  };
}

export function findCurrentUserApproval(
  ticket: ServiceDeskTicket,
  currentUserId: string,
): ServiceDeskTicketApproval | null {
  for (const stage of ticket.approval_stages) {
    if (stage.status !== "pending" || !stage.started_at) {
      continue;
    }
    const approval = stage.approvals.find(
      (item) =>
        item.approver_user_id === currentUserId && item.status === "pending",
    );
    if (approval) {
      return approval;
    }
  }
  return null;
}
