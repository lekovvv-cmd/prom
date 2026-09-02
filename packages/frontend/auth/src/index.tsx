import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { components as AccessContract } from "@prom/generated-contracts/access";

/** The identity returned by the platform Access service. */
export type PlatformUser = AccessContract["schemas"]["UserOut"];
export type PlatformModuleAccess = AccessContract["schemas"]["ModuleOut"];
export type PlatformAuthorization = {
  modules: PlatformModuleAccess[];
  permissions: string[];
};
export type AuthSession = PlatformAuthorization & { user: PlatformUser };

export type AuthContextValue = {
  user: PlatformUser | null;
  modules: PlatformModuleAccess[];
  permissions: string[];
  isAuthenticated: boolean;
  isAdmin: boolean;
  hasPermission: (permission: string) => boolean;
  isLoading: boolean;
  login: (session: AuthSession) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const EMPTY_AUTHORIZATION: PlatformAuthorization = {
  modules: [],
  permissions: [],
};

export function AuthProvider({
  children,
  loadSession,
  closeSession,
}: {
  children: React.ReactNode;
  loadSession: () => Promise<AuthSession>;
  closeSession: () => Promise<void>;
}) {
  const [user, setUser] = useState<PlatformUser | null>(null);
  const [authorization, setAuthorization] =
    useState<PlatformAuthorization>(EMPTY_AUTHORIZATION);
  const [isLoading, setIsLoading] = useState(true);

  const clearSession = useCallback(() => {
    setUser(null);
    setAuthorization(EMPTY_AUTHORIZATION);
  }, []);

  const logout = useCallback(() => {
    void closeSession().finally(clearSession);
  }, [clearSession, closeSession]);

  const refreshUser = useCallback(async () => {
    try {
      setIsLoading(true);
      const nextSession = await loadSession();
      setUser(nextSession.user);
      setAuthorization({
        modules: nextSession.modules,
        permissions: nextSession.permissions,
      });
    } catch {
      clearSession();
    } finally {
      setIsLoading(false);
    }
  }, [clearSession, loadSession]);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback((nextSession: AuthSession) => {
    setUser(nextSession.user);
    setAuthorization({
      modules: nextSession.modules,
      permissions: nextSession.permissions,
    });
  }, []);

  const isAuthenticated = user !== null;
  const { hasPermission, isAdmin } = createAuthFlags(authorization);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      modules: authorization.modules,
      permissions: authorization.permissions,
      isAuthenticated,
      isAdmin,
      hasPermission,
      isLoading,
      login,
      logout,
      refreshUser,
    }),
    [
      authorization.modules,
      authorization.permissions,
      isAdmin,
      isAuthenticated,
      isLoading,
      login,
      logout,
      refreshUser,
      user,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function createAuthFlags(authorization: PlatformAuthorization) {
  const hasPermission = (permission: string) =>
    authorization.permissions.includes(permission);
  return {
    hasPermission,
    isAdmin: hasPermission("platform.admin"),
  };
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
