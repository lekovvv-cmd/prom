import { createApiClient } from "./client";
import { env } from "./env";

export const apiClient = createApiClient(env.apiBaseUrl);
export const serviceDeskApiClient = createApiClient(env.serviceDeskApiBaseUrl);
export const accessApiClient = createApiClient(env.accessApiBaseUrl);
