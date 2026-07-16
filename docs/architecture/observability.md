# Observability

Backend request context adds `X-Request-ID` and emits structured JSON fields
for service, module, environment, event, duration, status, and actor when it
is safe. Tokens, cookies, secrets, and file contents are never logged.
OpenTelemetry configuration remains optional; a missing exporter must not stop
the application. Readiness checks validate dependencies while liveness remains
process-only.

