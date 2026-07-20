import type { PlatformAuthorization, User } from "../../index";

export type AuthCodeResponse = {
  email: string;
  dev_code: string;
  message: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  user: User;
} & PlatformAuthorization;
