export type FrontendErrorEvent = {
  error: unknown;
  moduleId?: string;
  componentStack?: string;
  route?: string;
  context?: Record<string, unknown>;
};

export type FrontendErrorReporter = {
  capture: (event: FrontendErrorEvent) => void;
};

const consoleReporter: FrontendErrorReporter = {
  capture(event) {
    console.error("PROM frontend error", event);
  },
};

let activeReporter: FrontendErrorReporter = consoleReporter;

export function configureFrontendErrorReporter(
  reporter: FrontendErrorReporter,
) {
  activeReporter = reporter;
}

export function reportFrontendError(event: FrontendErrorEvent) {
  activeReporter.capture(event);
}
