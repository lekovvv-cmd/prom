import type {
  AuthSession,
  PlatformAuthorization,
  User,
  UserProfilePayload,
} from "./index";
import { accessApiClient, apiClient } from "@prom/api-client";
import type { components as AccessContract } from "@prom/generated-contracts/access";

export function getMe() {
  return apiClient.request<User>("/me");
}

function toLegacyUser(
  user: AccessContract["schemas"]["UserOut"],
  permissions: string[],
): User {
  const role = permissions.includes("platform.admin")
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

export async function getAccessSession(): Promise<AuthSession> {
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

export function getAdminUsers() {
  return apiClient.request<User[]>("/admin/users");
}

export function getUserDirectory(search?: string) {
  const query = search ? `?${new URLSearchParams({ search }).toString()}` : "";
  return apiClient.request<User[]>(`/users/directory${query}`);
}

export function updateMyProfile(payload: UserProfilePayload) {
  return apiClient.request<User>("/me/profile", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}
