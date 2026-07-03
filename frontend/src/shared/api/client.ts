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

const VALIDATION_FIELD_LABELS: Record<string, string> = {
  full_name: "ФИО",
  email: "Email",
  contact_email: "Контактный email",
  comment: "Комментарий",
  competencies: "Компетенции",
  title: "Название",
  short_description: "Краткое описание",
  description: "Описание",
  goal: "Цель",
  expected_result: "Ожидаемый результат"
};

type ApiValidationError = {
  loc?: unknown[];
  msg?: unknown;
  type?: unknown;
  ctx?: {
    min_length?: unknown;
  };
};

function getValidationField(error: ApiValidationError) {
  if (!Array.isArray(error.loc)) {
    return null;
  }
  const field = [...error.loc].reverse().find((item) => typeof item === "string" && item !== "body");
  return typeof field === "string" ? field : null;
}

function normalizeValidationMessage(error: ApiValidationError) {
  const field = getValidationField(error);
  const type = typeof error.type === "string" ? error.type : "";
  const rawMessage = typeof error.msg === "string" ? error.msg.replace(/^Value error,\s*/i, "") : "";

  if (field === "full_name" && (type.includes("too_short") || rawMessage.includes("at least 2"))) {
    return "ФИО: укажите ФИО не короче 2 символов";
  }

  if (type.includes("too_short")) {
    const label = field && VALIDATION_FIELD_LABELS[field] ? VALIDATION_FIELD_LABELS[field] : "Поле";
    const minLength = typeof error.ctx?.min_length === "number" ? error.ctx.min_length : null;
    return minLength ? `${label}: заполните поле минимум ${minLength} символами` : `${label}: значение слишком короткое`;
  }

  if (type === "missing") {
    return field && VALIDATION_FIELD_LABELS[field]
      ? `${VALIDATION_FIELD_LABELS[field]}: заполните поле`
      : "Заполните обязательные поля";
  }

  if (rawMessage) {
    return field && VALIDATION_FIELD_LABELS[field] ? `${VALIDATION_FIELD_LABELS[field]}: ${rawMessage}` : rawMessage;
  }

  return field && VALIDATION_FIELD_LABELS[field]
    ? `${VALIDATION_FIELD_LABELS[field]}: некорректное значение`
    : "Некорректные данные формы";
}

export function normalizeApiErrorMessage(payload: unknown) {
  if (!payload || typeof payload !== "object") {
    return "Ошибка API";
  }

  const detail = "detail" in payload ? (payload as { detail?: unknown }).detail : null;
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail.map((item) => normalizeValidationMessage(item as ApiValidationError));
    return [...new Set(messages)].join(". ") || "Некорректные данные формы";
  }

  if (detail && typeof detail === "object" && "msg" in detail) {
    return normalizeValidationMessage(detail as ApiValidationError);
  }

  return "Ошибка API";
}

async function parseResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json") ? await response.json() : null;
  if (!response.ok) {
    const message = normalizeApiErrorMessage(payload);
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
