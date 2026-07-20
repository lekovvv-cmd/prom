const TOKEN_KEY = "shpiu_project_showcase_token";

export type AuthTokenStorage = {
  getToken: () => string | null;
  setToken: (token: string | null) => void;
};

export const authTokenStorage: AuthTokenStorage = {
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
};
