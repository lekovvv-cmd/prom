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
  expected_result: "Ожидаемый результат",
  project_type: "Тип проекта",
  priority: "Приоритет",
  status: "Статус",
  sort: "Сортировка",
  responsible_user_id: "Ответственный",
  working_group_member_ids: "Рабочая группа",
  start_date: "Дата начала",
  end_date: "Дата окончания"
};

const VALIDATION_VALUE_LABELS: Record<string, string> = {
  strategic: "Стратегический",
  low: "Низкий",
  medium: "Средний",
  high: "Высокий",
  critical: "Критичный",
  draft: "Черновик",
  active: "Активен",
  paused: "Пауза",
  completed: "Завершен",
  archived: "Архив",
  created_at_desc: "Сначала новые",
  created_at_asc: "Сначала старые",
  priority_desc: "Высокий приоритет",
  priority_asc: "Низкий приоритет",
  new: "Новый",
  viewed: "Просмотрен",
  contacted: "Связались",
  accepted: "Принят",
  rejected: "Отклонен",
  cancelled: "Отозван"
};

type ApiValidationError = {
  loc?: unknown[];
  msg?: unknown;
  type?: unknown;
  ctx?: {
    min_length?: unknown;
    expected?: unknown;
  };
};

function getValidationField(error: ApiValidationError) {
  if (!Array.isArray(error.loc)) {
    return null;
  }
  const field = [...error.loc].reverse().find((item) => typeof item === "string" && item !== "body");
  return typeof field === "string" ? field : null;
}

function getFieldLabel(field: string | null) {
  return field && VALIDATION_FIELD_LABELS[field] ? VALIDATION_FIELD_LABELS[field] : "Поле";
}

function getExpectedValues(error: ApiValidationError, rawMessage: string) {
  const expected = typeof error.ctx?.expected === "string" ? error.ctx.expected : rawMessage;
  return Array.from(expected.matchAll(/'([^']+)'/g), (match) => match[1]);
}

function formatExpectedValues(values: string[]) {
  return values.map((value) => VALIDATION_VALUE_LABELS[value] ?? value).join(", ");
}

function looksLikeEnglishValidationMessage(message: string) {
  return /[a-z]/i.test(message) && !/[а-яё]/i.test(message);
}

function normalizeValidationMessage(error: ApiValidationError) {
  const field = getValidationField(error);
  const type = typeof error.type === "string" ? error.type : "";
  const rawMessage = typeof error.msg === "string" ? error.msg.replace(/^Value error,\s*/i, "") : "";
  const label = getFieldLabel(field);

  if (field === "full_name" && (type.includes("too_short") || rawMessage.includes("at least 2"))) {
    return "ФИО: укажите ФИО не короче 2 символов";
  }

  if (type.includes("too_short")) {
    const minLength = typeof error.ctx?.min_length === "number" ? error.ctx.min_length : null;
    return minLength ? `${label}: заполните поле минимум ${minLength} символами` : `${label}: значение слишком короткое`;
  }

  if (type === "missing") {
    return field && VALIDATION_FIELD_LABELS[field]
      ? `${VALIDATION_FIELD_LABELS[field]}: заполните поле`
      : "Заполните обязательные поля";
  }

  const expectedValues = getExpectedValues(error, rawMessage);
  if (type.includes("enum") || type.includes("literal") || expectedValues.length > 0) {
    const expectedText = expectedValues.length > 0 ? `: ${formatExpectedValues(expectedValues)}` : "";
    return `${label}: выберите значение из списка${expectedText}`;
  }

  if (type.includes("uuid")) {
    return `${label}: некорректный идентификатор`;
  }

  if (type.includes("date")) {
    return `${label}: укажите дату в формате ГГГГ-ММ-ДД`;
  }

  if (rawMessage) {
    if (looksLikeEnglishValidationMessage(rawMessage)) {
      return `${label}: некорректное значение`;
    }
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
