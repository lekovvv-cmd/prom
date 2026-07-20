import type { PlatformAuthorization, User, UserProfilePayload } from "./index";
import { accessApiClient, apiClient } from "@prom/api-client";
import type { components as AccessContract } from "@prom/generated-contracts/access";

export function getMe() {
  return apiClient.request<User>("/me");
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
