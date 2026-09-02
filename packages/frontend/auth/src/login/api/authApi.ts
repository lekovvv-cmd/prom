import { accessApiClient } from "@prom/api-client";
import type { components as AccessContract } from "@prom/generated-contracts/access";
import type { AuthCodeResponse, SessionResponse } from "../model/types";

export function requestCode(email: string) {
  return accessApiClient.request<AuthCodeResponse>("/auth/mock/code", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email }),
  });
}

export async function verifyCode(
  email: string,
  code: string,
): Promise<SessionResponse> {
  await accessApiClient.request<AccessContract["schemas"]["SessionOut"]>(
    "/auth/mock/verify",
    {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email, code }),
    },
  );
  const response =
    await accessApiClient.request<AccessContract["schemas"]["TokenOut"]>(
      "/session/token",
    );
  accessApiClient.setToken(response.access_token);
  const session = response.session;
  return {
    user: session.user,
    modules: session.modules,
    permissions: session.permissions,
  };
}
