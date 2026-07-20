import type { ServiceDeskTicketComment } from "../../../entities/service-desk-ticket/model/types";
import { serviceDeskApiClient } from "@prom/api-client";

export function addTicketComment(
  ticketId: string,
  payload: { body: string; visibility: "public" | "internal" },
) {
  return serviceDeskApiClient.request<ServiceDeskTicketComment>(
    `/tickets/${ticketId}/comments`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}
