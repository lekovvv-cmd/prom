import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { getCurrentServiceDeskUser } from "../../entities/service-desk-user/api/serviceDeskUserApi";
import type { ServiceDeskUser } from "../../entities/service-desk-user/model/types";

type ServiceDeskAccessContextValue = {
  user: ServiceDeskUser | null;
  isLoading: boolean;
  error: string | null;
};

const ServiceDeskAccessContext = createContext<ServiceDeskAccessContextValue | null>(null);

export function ServiceDeskAccessProvider({
  children,
  token
}: {
  children: React.ReactNode;
  token: string | null;
}) {
  const [user, setUser] = useState<ServiceDeskUser | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isCurrent = true;
    if (!token) {
      setUser(null);
      setError(null);
      setIsLoading(false);
      return () => {
        isCurrent = false;
      };
    }

    setIsLoading(true);
    setUser(null);
    setError(null);
    void getCurrentServiceDeskUser()
      .then((currentUser) => {
        if (isCurrent) {
          setUser(currentUser);
        }
      })
      .catch((requestError: unknown) => {
        if (isCurrent) {
          setUser(null);
          setError(
            requestError instanceof Error ? requestError.message : "Нет доступа к Service Desk"
          );
        }
      })
      .finally(() => {
        if (isCurrent) {
          setIsLoading(false);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [token]);

  const isResolving = Boolean(token && !user && !error);
  const value = useMemo(
    () => ({ user, isLoading: isLoading || isResolving, error }),
    [error, isLoading, isResolving, user]
  );

  return (
    <ServiceDeskAccessContext.Provider value={value}>
      {children}
    </ServiceDeskAccessContext.Provider>
  );
}

export function useServiceDeskAccess() {
  const context = useContext(ServiceDeskAccessContext);
  if (!context) {
    throw new Error("useServiceDeskAccess must be used within ServiceDeskAccessProvider");
  }
  return context;
}
