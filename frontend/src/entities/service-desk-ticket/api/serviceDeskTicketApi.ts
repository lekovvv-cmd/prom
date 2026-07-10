import { serviceDeskApiClient } from "../../../shared/api/client";
import type { ServiceDeskTicket } from "../model/types";

export function getServiceDeskTicket(ticketId: string) {
  return serviceDeskApiClient.request<ServiceDeskTicket>(`/tickets/${ticketId}`);
}
