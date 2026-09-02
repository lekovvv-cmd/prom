import { beforeEach, describe, expect, it, vi } from "vitest";
const { accessRequest, accessSetToken } = vi.hoisted(() => ({
  accessRequest: vi.fn(),
  accessSetToken: vi.fn(),
}));
vi.mock("@prom/api-client", () => ({
  accessApiClient: { request: accessRequest, setToken: accessSetToken },
}));
import {
  closeAccessSession,
  getAccessSession,
  getPlatformAuthorization,
} from "./api";
import { createAuthFlags } from "./index";
describe("getPlatformAuthorization", () => {
  beforeEach(() => {
    accessRequest.mockReset();
    accessSetToken.mockReset();
  });
  it("uses a path relative to the versioned Access API base URL", async () => {
    accessRequest.mockResolvedValue({
      modules: [{ id: "service-desk" }],
      permissions: ["service_desk.access"],
    });
    await expect(getPlatformAuthorization()).resolves.toEqual({
      modules: [{ id: "service-desk" }],
      permissions: ["service_desk.access"],
    });
    expect(accessRequest).toHaveBeenCalledWith("/session");
  });
  it("probes an optional cookie session without an anonymous 401", async () => {
    accessRequest.mockResolvedValue({ authenticated: false, token: null });
    await expect(getAccessSession()).rejects.toThrow(
      "No authenticated browser session",
    );
    expect(accessRequest).toHaveBeenCalledWith("/session/probe", {
      auth: false,
    });
    expect(accessSetToken).toHaveBeenCalledWith(null);
  });
  it("keeps the Access identity and short bearer after a successful probe", async () => {
    accessRequest.mockResolvedValue({
      authenticated: true,
      token: {
        access_token: "short-bearer",
        session: {
          user: {
            id: "user-1",
            email: "user@utmn.ru",
            display_name: "User",
            department: null,
            position: null,
          },
          modules: [
            { id: "service-desk", permissions: ["service_desk.access"] },
          ],
          permissions: ["service_desk.access"],
        },
      },
    });
    await expect(getAccessSession()).resolves.toEqual({
      user: {
        id: "user-1",
        email: "user@utmn.ru",
        display_name: "User",
        department: null,
        position: null,
      },
      modules: [{ id: "service-desk", permissions: ["service_desk.access"] }],
      permissions: ["service_desk.access"],
    });
    expect(accessSetToken).toHaveBeenCalledWith("short-bearer");
  });

  it("closes the browser session and clears the in-memory bearer", async () => {
    accessRequest.mockResolvedValue(undefined);

    await closeAccessSession();

    expect(accessRequest).toHaveBeenCalledWith("/session", {
      method: "DELETE",
    });
    expect(accessSetToken).toHaveBeenCalledWith(null);
  });
});
describe("platform authorization flags", () => {
  it("derives isAdmin from platform.admin and keeps permission checks generic", () => {
    const flags = createAuthFlags({
      modules: [],
      permissions: ["platform.admin", "service_desk.access"],
    });
    expect(flags.isAdmin).toBe(true);
    expect(flags.hasPermission("service_desk.access")).toBe(true);
    expect(flags.hasPermission("missing.permission")).toBe(false);
  });
});
