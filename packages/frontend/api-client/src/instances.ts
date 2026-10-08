import { ApiError, createApiClient } from "./client";
import { env } from "./env";
import { authTokenStorage } from "./authTokenStorage";

let renewal: Promise<string> | null = null;

export function renewAccessToken(): Promise<string> {
  if (!renewal) {
    renewal = (async () => {
      const response = await fetch(`${env.accessApiBaseUrl}/session/token`, {
        credentials: "include",
      });
      if (!response.ok) {
        if (response.status === 401) {
          authTokenStorage.setToken(null);
          if (typeof window !== "undefined") {
            window.dispatchEvent(new Event("prom:session-expired"));
          }
        }
        throw new ApiError({
          status: response.status,
          code:
            response.status === 401
              ? "SESSION_EXPIRED"
              : "SESSION_RENEWAL_FAILED",
          message:
            response.status === 401
              ? "Сессия истекла, войдите снова"
              : "Не удалось продлить сессию",
        });
      }
      const payload = (await response.json()) as { access_token: string };
      authTokenStorage.setToken(payload.access_token);
      return payload.access_token;
    })().finally(() => {
      renewal = null;
    });
  }
  return renewal;
}

export const apiClient = createApiClient(
  env.apiBaseUrl,
  authTokenStorage,
  renewAccessToken,
);
export const serviceDeskApiClient = createApiClient(
  env.serviceDeskApiBaseUrl,
  authTokenStorage,
  renewAccessToken,
);
export const accessApiClient = createApiClient(
  env.accessApiBaseUrl,
  authTokenStorage,
  renewAccessToken,
);
