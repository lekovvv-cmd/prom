import { apiClient } from "../../../shared/api/client";
import type { AuthCodeResponse, TokenResponse } from "../model/types";

export function requestCode(email: string) {
  return apiClient.request<AuthCodeResponse>("/auth/request-code", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email })
  });
}

export function verifyCode(email: string, code: string) {
  return apiClient.request<TokenResponse>("/auth/verify-code", {
    method: "POST",
    auth: false,
    body: JSON.stringify({ email, code })
  });
}
