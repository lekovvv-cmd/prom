import type { AuthSession } from "../../index";

export type AuthCodeResponse = {
  email: string;
  dev_code: string;
};

export type SessionResponse = AuthSession;
