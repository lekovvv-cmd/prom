import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { AppProviders } from "./providers/AppProviders";
import { AppRouter } from "./routes/AppRouter";
import "./styles/globals.css";
import "@prom/ui/styles.css";
import "@prom/layout/styles.css";

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <AppProviders>
      <AppRouter />
    </AppProviders>
  </StrictMode>,
);
