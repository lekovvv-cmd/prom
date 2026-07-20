import { Component, type ErrorInfo, type ReactNode } from "react";
import { reportFrontendError } from "@prom/observability";

import { Button } from "./Button";
import { Card } from "./Card";

type ModuleErrorBoundaryProps = {
  children: ReactNode;
  moduleId: string;
  moduleName: string;
};

type ModuleErrorBoundaryState = {
  error: Error | null;
};

export class ModuleErrorBoundary extends Component<
  ModuleErrorBoundaryProps,
  ModuleErrorBoundaryState
> {
  state: ModuleErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ModuleErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    reportFrontendError({
      error,
      moduleId: this.props.moduleId,
      componentStack: info.componentStack ?? undefined,
      route: window.location.pathname,
    });
  }

  render() {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <main className="module-error-page">
        <Card>
          <h1>Не удалось открыть модуль «{this.props.moduleName}»</h1>
          <p className="muted" role="alert">
            Ошибка зарегистрирована. Обновите страницу и повторите попытку.
          </p>
          <Button onClick={() => window.location.reload()}>
            Обновить страницу
          </Button>
        </Card>
      </main>
    );
  }
}
