export type AuthTokenStorage = {
  getToken: () => string | null;
  setToken: (token: string | null) => void;
};

let volatileToken: string | null = null;

/** Bearer tokens are intentionally memory-only and are used by tests or non-browser callers. */
export const authTokenStorage: AuthTokenStorage = {
  getToken() {
    return volatileToken;
  },
  setToken(token: string | null) {
    volatileToken = token;
  },
};
