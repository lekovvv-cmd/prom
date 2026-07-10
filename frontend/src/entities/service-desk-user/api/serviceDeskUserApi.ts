import { serviceDeskApiClient } from "../../../shared/api/client";
import type { ServiceDeskUser } from "../model/types";

export function getCurrentServiceDeskUser() {
  return serviceDeskApiClient.request<ServiceDeskUser>("/me");
}
