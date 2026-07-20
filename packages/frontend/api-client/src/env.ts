const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export const env = {
  apiBaseUrl,
  serviceDeskApiBaseUrl:
    import.meta.env.VITE_SERVICE_DESK_API_BASE_URL ?? "http://localhost:8001",
  accessApiBaseUrl:
    import.meta.env.VITE_ACCESS_API_BASE_URL ?? "http://localhost:8002",
  // The gateway maps project downloads under the same versioned namespace as the API.
  fileBaseUrl: apiBaseUrl.endsWith("/api")
    ? apiBaseUrl.slice(0, -4)
    : apiBaseUrl,
};
