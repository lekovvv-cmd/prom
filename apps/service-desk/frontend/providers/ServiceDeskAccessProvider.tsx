import { createContext, useContext, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  getCurrentServiceDeskUser,
  getServiceDeskAccessStatus,
} from "../entities/service-desk-user/api/serviceDeskUserApi";
import type { ServiceDeskUser } from "../entities/service-desk-user/model/types";
import { serviceDeskQueryKeys } from "../api/queryKeys";

type ServiceDeskAccessContextValue = {
  user: ServiceDeskUser | null;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
};

const ServiceDeskAccessContext =
  createContext<ServiceDeskAccessContextValue | null>(null);

async function fetchServiceDeskAccess(): Promise<ServiceDeskUser> {
  const { has_access: hasAccess } = await getServiceDeskAccessStatus();
  if (!hasAccess)
    throw new Error("У вашей учётной записи нет доступа к Service Desk.");
  return getCurrentServiceDeskUser();
}

export function ServiceDeskAccessProvider({
  children,
  token,
}: {
  children: React.ReactNode;
  token: string | null;
}) {
  const query = useQuery({
    queryKey: serviceDeskQueryKeys.access(token),
    queryFn: fetchServiceDeskAccess,
    enabled: Boolean(token),
    staleTime: 60_000,
    retry: 0,
  });
  const value = useMemo<ServiceDeskAccessContextValue>(
    () => ({
      user: token ? (query.data ?? null) : null,
      isLoading: Boolean(token) && query.isLoading,
      error:
        query.error instanceof Error
          ? query.error.message
          : query.error
            ? "Нет доступа к Service Desk"
            : null,
      refresh: async () => {
        await query.refetch();
      },
    }),
    [query.data, query.error, query.isLoading, query.refetch, token],
  );
  return (
    <ServiceDeskAccessContext.Provider value={value}>
      {children}
    </ServiceDeskAccessContext.Provider>
  );
}

export function useServiceDeskAccess() {
  const context = useContext(ServiceDeskAccessContext);
  return (
    context ?? {
      user: null,
      isLoading: false,
      error: null,
      refresh: async () => undefined,
    }
  );
}
