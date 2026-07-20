import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@prom/auth";
import { getMe, getPlatformAuthorization } from "@prom/auth/api";
import { useState } from "react";
import { BrowserRouter } from "react-router-dom";

import { apiClient } from "@prom/api-client";

export function AppProviders({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
          mutations: { retry: 0 },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider
          client={apiClient}
          loadAuthorization={getPlatformAuthorization}
          loadCurrentUser={getMe}
        >
          {children}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
