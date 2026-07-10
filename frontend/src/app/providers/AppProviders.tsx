import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { BrowserRouter } from "react-router-dom";

import { getMe } from "../../entities/user/api/userApi";
import type { User } from "../../entities/user/model/types";
import { apiClient } from "../../shared/api/client";
import { ServiceDeskAccessProvider } from "./ServiceDeskAccessProvider";

type AuthContextValue = {
  token: string | null;
  user: User | null;
  isAdmin: boolean;
  canManageProjects: boolean;
  isLoading: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => apiClient.getToken());
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(token));

  const logout = useCallback(() => {
    apiClient.setToken(null);
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!apiClient.getToken()) {
      setIsLoading(false);
      return;
    }
    try {
      setIsLoading(true);
      const currentUser = await getMe();
      setUser(currentUser);
    } catch {
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback((nextToken: string, nextUser: User) => {
    apiClient.setToken(nextToken);
    setToken(nextToken);
    setUser(nextUser);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      isAdmin: user?.role === "admin",
      canManageProjects: user?.role === "admin" || user?.role === "project_manager",
      isLoading,
      login,
      logout,
      refreshUser
    }),
    [isLoading, login, logout, refreshUser, token, user]
  );

  return (
    <BrowserRouter>
      <AuthContext.Provider value={value}>
        <ServiceDeskAccessProvider token={token}>{children}</ServiceDeskAccessProvider>
      </AuthContext.Provider>
    </BrowserRouter>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AppProviders");
  }
  return context;
}
