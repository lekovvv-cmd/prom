import { accessApiClient } from "@prom/api-client";
import type { components as AccessContract } from "@prom/generated-contracts/access";
import type { User, UserRole } from "../../index";
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
    user: toLegacyUser(session.user, session.permissions),
    modules: session.modules,
    permissions: session.permissions,
  };
}

function toLegacyUser(
  user: AccessContract["schemas"]["UserOut"],
  permissions: string[],
): User {
  const role: UserRole = permissions.includes("platform.admin")
    ? "platform_admin"
    : permissions.includes("projects.create")
      ? "project_manager"
      : "employee";
  const now = new Date().toISOString();
  return {
    id: user.id,
    email: user.email,
    full_name: user.display_name,
    role,
    department: user.department,
    position: user.position,
    created_at: now,
    updated_at: now,
  };
}
