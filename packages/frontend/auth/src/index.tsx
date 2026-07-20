import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { components as ProjectsContract } from "@prom/generated-contracts/projects";
import type { components as AccessContract } from "@prom/generated-contracts/access";

export type UserRole = ProjectsContract["schemas"]["UserRole"];
export type User = ProjectsContract["schemas"]["UserRead"];
export type UserProfilePayload =
  ProjectsContract["schemas"]["UserProfileUpdate"];
export type PlatformModuleAccess = AccessContract["schemas"]["ModuleOut"];
export type PlatformAuthorization = {
  modules: PlatformModuleAccess[];
  permissions: string[];
};

export type AuthTokenClient = {
  getToken: () => string | null;
  setToken: (token: string | null) => void;
};

export type AuthContextValue = {
  token: string | null;
  user: User | null;
  modules: PlatformModuleAccess[];
  permissions: string[];
  isAdmin: boolean;
  canManageProjects: boolean;
  hasPermission: (permission: string) => boolean;
  isLoading: boolean;
  login: (
    token: string,
    user: User,
    authorization?: PlatformAuthorization,
  ) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  children,
  client,
  loadAuthorization,
  loadCurrentUser,
}: {
  children: React.ReactNode;
  client: AuthTokenClient;
  loadAuthorization?: () => Promise<PlatformAuthorization>;
  loadCurrentUser: () => Promise<User>;
}) {
  const [token, setToken] = useState<string | null>(() => client.getToken());
  const [user, setUser] = useState<User | null>(null);
  const [authorization, setAuthorization] = useState<PlatformAuthorization>({
    modules: [],
    permissions: [],
  });
  const [isLoading, setIsLoading] = useState(Boolean(token));

  const logout = useCallback(() => {
    client.setToken(null);
    setToken(null);
    setUser(null);
    setAuthorization({ modules: [], permissions: [] });
  }, [client]);

  const refreshUser = useCallback(async () => {
    if (!client.getToken()) {
      setIsLoading(false);
      return;
    }
    try {
      setIsLoading(true);
      const [nextUser, nextAuthorization] = await Promise.all([
        loadCurrentUser(),
        loadAuthorization?.() ??
          Promise.resolve({ modules: [], permissions: [] }),
      ]);
      setUser(nextUser);
      setAuthorization(nextAuthorization);
    } catch {
      logout();
    } finally {
      setIsLoading(false);
    }
  }, [client, loadAuthorization, loadCurrentUser, logout]);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    (
      nextToken: string,
      nextUser: User,
      nextAuthorization?: PlatformAuthorization,
    ) => {
      client.setToken(nextToken);
      setToken(nextToken);
      setUser(nextUser);
      setAuthorization(nextAuthorization ?? { modules: [], permissions: [] });
    },
    [client],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      modules: authorization.modules,
      permissions: authorization.permissions,
      isAdmin:
        authorization.permissions.includes("platform.admin") ||
        user?.role === "platform_admin",
      canManageProjects:
        authorization.permissions.includes("projects.create") ||
        authorization.permissions.includes("projects.manage") ||
        user?.role === "platform_admin" ||
        user?.role === "project_manager",
      hasPermission: (permission) =>
        authorization.permissions.includes(permission),
      isLoading,
      login,
      logout,
      refreshUser,
    }),
    [authorization, isLoading, login, logout, refreshUser, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
