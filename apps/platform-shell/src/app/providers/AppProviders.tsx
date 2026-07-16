import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { getMe } from "../../entities/user/api/userApi";
import type { User } from "../../entities/user/model/types";
import { apiClient } from "../../shared/api/client";

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
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
      mutations: { retry: 0 }
    }
  }));
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
      isAdmin: user?.role === "platform_admin",
      canManageProjects: user?.role === "platform_admin" || user?.role === "project_manager",
      isLoading,
      login,
      logout,
      refreshUser
    }),
    [isLoading, login, logout, refreshUser, token, user]
  );

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AppProviders");
  }
  return context;
}
