export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
  serviceDeskApiBaseUrl: import.meta.env.VITE_SERVICE_DESK_API_BASE_URL ?? "http://localhost:8001",
  fileBaseUrl: (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api").replace(/\/api\/?$/, "")
};
