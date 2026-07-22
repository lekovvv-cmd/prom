import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@prom/auth";
import { closeAccessSession, getAccessSession } from "@prom/auth/api";
import { useState } from "react";
import { BrowserRouter } from "react-router-dom";

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
          loadSession={getAccessSession}
          closeSession={closeAccessSession}
        >
          {children}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
