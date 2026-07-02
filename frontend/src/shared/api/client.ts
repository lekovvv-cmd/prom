import { env } from "../config/env";

const TOKEN_KEY = "shpiu_project_showcase_token";

type RequestOptions = RequestInit & {
  auth?: boolean;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const message = payload?.detail ?? "Ошибка API";
    throw new ApiError(message, response.status);
  }
  return payload as T;
}

export const apiClient = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken(token: string | null) {
    if (token) {
      localStorage.setItem(TOKEN_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
  },
  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (!headers.has("Content-Type") && options.body && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    const token = this.getToken();
    if (token && options.auth !== false) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    const response = await fetch(`${env.apiBaseUrl}${path}`, {
      ...options,
      headers
    });
    return parseResponse<T>(response);
  }
};
