import { authTokenStorage, type AuthTokenStorage } from "./authTokenStorage";

export type RequestOptions = RequestInit & {
  auth?: boolean;
  timeoutMs?: number;
};

export type ApiFieldError = {
  field: string | null;
  message: string;
  code: string | null;
};

type ProblemDetails = {
  status?: unknown;
  code?: unknown;
  type?: unknown;
  title?: unknown;
  detail?: unknown;
  request_id?: unknown;
  requestId?: unknown;
  errors?: unknown;
};

const NETWORK_ERROR_MESSAGE =
  "Не удалось связаться с сервером. Проверьте подключение и попробуйте ещё раз.";
const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly type: string | null;
  readonly requestId: string | null;
  readonly fieldErrors: ApiFieldError[];
  readonly rawDetails: unknown;
  readonly details: unknown;

  constructor({
    message,
    status,
    code = null,
    type = null,
    requestId = null,
    fieldErrors = [],
    rawDetails = null,
  }: {
    message: string;
    status: number;
    code?: string | null;
    type?: string | null;
    requestId?: string | null;
    fieldErrors?: ApiFieldError[];
    rawDetails?: unknown;
  }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.type = type;
    this.requestId = requestId;
    this.fieldErrors = fieldErrors;
    this.rawDetails = rawDetails;
    this.details = rawDetails;
  }
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function fieldName(location: unknown): string | null {
  if (!Array.isArray(location)) return null;
  const field = [...location]
    .reverse()
    .find((part) => typeof part === "string" && part !== "body");
  return typeof field === "string" ? field : null;
}

function parseFieldErrors(payload: ProblemDetails): ApiFieldError[] {
  const source = Array.isArray(payload.errors)
    ? payload.errors
    : Array.isArray(payload.detail)
      ? payload.detail
      : [];
  return source.flatMap((item) => {
    if (!item || typeof item !== "object") return [];
    const value = item as Record<string, unknown>;
    const message = stringValue(value.message) ?? stringValue(value.msg);
    if (!message) return [];
    return [
      {
        field:
          stringValue(value.field) ??
          stringValue(value.field_key) ??
          fieldName(value.loc),
        message,
        code: stringValue(value.code) ?? stringValue(value.type),
      },
    ];
  });
}

export function normalizeApiErrorMessage(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "Ошибка API";
  const problem = payload as ProblemDetails;
  const detail = stringValue(problem.detail);
  if (detail) return detail;
  const title = stringValue(problem.title);
  if (title) return title;
  const fieldErrors = parseFieldErrors(problem);
  if (fieldErrors.length > 0) {
    return fieldErrors.map((error) => error.message).join(". ");
  }
  return "Ошибка API";
}

function toApiError(response: Response, payload: unknown): ApiError {
  const problem =
    payload && typeof payload === "object"
      ? (payload as ProblemDetails)
      : ({} satisfies ProblemDetails);
  return new ApiError({
    message: normalizeApiErrorMessage(payload),
    status: response.status,
    code: stringValue(problem.code),
    type: stringValue(problem.type),
    requestId:
      stringValue(problem.request_id) ??
      stringValue(problem.requestId) ??
      response.headers.get("x-request-id"),
    fieldErrors: parseFieldErrors(problem),
    rawDetails: payload,
  });
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") ?? "";
  const isJson =
    contentType.includes("application/json") || contentType.includes("+json");
  const payload = isJson ? await response.json() : null;
  if (!response.ok) throw toApiError(response, payload);
  return payload as T;
}

function csrfToken(): string | null {
  if (typeof document === "undefined") return null;
  for (const item of document.cookie.split(";")) {
    const [name, ...value] = item.trim().split("=");
    if (name === "prom_csrf") return decodeURIComponent(value.join("="));
  }
  return null;
}

export function createApiClient(
  baseUrl: string,
  tokenStorage: AuthTokenStorage = authTokenStorage,
) {
  return {
    getToken() {
      return tokenStorage.getToken();
    },
    setToken(token: string | null) {
      tokenStorage.setToken(token);
    },
    async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
      const { auth = true, timeoutMs = 15_000, ...requestInit } = options;
      const headers = new Headers(requestInit.headers);
      if (
        !headers.has("Content-Type") &&
        requestInit.body &&
        !(requestInit.body instanceof FormData)
      ) {
        headers.set("Content-Type", "application/json");
      }
      const token = tokenStorage.getToken();
      if (token && auth) headers.set("Authorization", `Bearer ${token}`);
      const method = (requestInit.method ?? "GET").toUpperCase();
      const csrf = csrfToken();
      if (auth && csrf && UNSAFE_METHODS.has(method)) {
        headers.set("X-CSRF-Token", csrf);
      }
      const controller = new AbortController();
      const timeout = globalThis.setTimeout(
        () => controller.abort(),
        timeoutMs,
      );
      const abortFromCaller = () => controller.abort();
      requestInit.signal?.addEventListener("abort", abortFromCaller, {
        once: true,
      });
      try {
        const response = await fetch(`${baseUrl}${path}`, {
          ...requestInit,
          headers,
          credentials: requestInit.credentials ?? "include",
          signal: controller.signal,
        });
        return await parseResponse<T>(response);
      } catch (reason) {
        if (reason instanceof ApiError) throw reason;
        const message =
          reason instanceof Error &&
          /failed to fetch|network(?:\s+request)?\s+failed|networkerror/i.test(
            reason.message,
          )
            ? NETWORK_ERROR_MESSAGE
            : "Не удалось выполнить запрос. Попробуйте ещё раз.";
        throw new ApiError({ message, status: 0, rawDetails: reason });
      } finally {
        globalThis.clearTimeout(timeout);
        requestInit.signal?.removeEventListener("abort", abortFromCaller);
      }
    },
  };
}
