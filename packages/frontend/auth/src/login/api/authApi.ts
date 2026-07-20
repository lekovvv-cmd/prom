import { accessApiClient } from "@prom/api-client";
import type { components as AccessContract } from "@prom/generated-contracts/access";
import type { User, UserRole } from "../../index";
import type { AuthCodeResponse, TokenResponse } from "../model/types";

export function requestCode(email: string) {
  return Promise.resolve({
    email,
    dev_code: "000000",
    message: "Local SSO mock is ready",
  } satisfies AuthCodeResponse);
}

export function verifyCode(email: string, code: string) {
  if (code !== "000000")
    return Promise.reject(new Error("Неверный код подтверждения"));
  return accessApiClient
    .request<AccessContract["schemas"]["TokenOut"]>("/auth/mock/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email }),
    })
    .then(
      (response) =>
        ({
          access_token: response.access_token,
          token_type: "bearer",
          user: toLegacyUser(
            response.session.user,
            response.session.permissions,
          ),
          modules: response.session.modules,
          permissions: response.session.permissions,
        }) satisfies TokenResponse,
    );
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
