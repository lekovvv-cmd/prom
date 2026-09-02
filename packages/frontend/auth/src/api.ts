import type { AuthSession, PlatformAuthorization } from "./index";
import { accessApiClient } from "@prom/api-client";
import type { components as AccessContract } from "@prom/generated-contracts/access";

export async function getAccessSession(): Promise<AuthSession> {
  const probe = await accessApiClient.request<
    AccessContract["schemas"]["SessionProbeOut"]
  >("/session/probe", { auth: false });
  if (!probe.authenticated || !probe.token) {
    accessApiClient.setToken(null);
    throw new Error("No authenticated browser session");
  }
  accessApiClient.setToken(probe.token.access_token);
  const session = probe.token.session;
  return {
    user: session.user,
    modules: session.modules,
    permissions: session.permissions,
  };
}

export async function closeAccessSession() {
  try {
    await accessApiClient.request<void>("/session", { method: "DELETE" });
  } finally {
    accessApiClient.setToken(null);
  }
}

export async function getPlatformAuthorization(): Promise<PlatformAuthorization> {
  const session =
    await accessApiClient.request<AccessContract["schemas"]["SessionOut"]>(
      "/session",
    );
  return { modules: session.modules, permissions: session.permissions };
}
