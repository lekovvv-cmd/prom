import type { ServiceDeskTicket } from "../../../entities/service-desk-ticket/model/types";
import { serviceDeskApiClient } from "../../../shared/api/client";

export function approveTicket(ticketId: string, approvalId: string, comment?: string) {
  return serviceDeskApiClient.request<ServiceDeskTicket>(
    `/tickets/${ticketId}/approvals/${approvalId}/approve`,
    {
      method: "POST",
      body: JSON.stringify({ comment: comment || null })
    }
  );
}
