# Observability

Backend request context adds `X-Request-ID` and emits structured JSON fields
for service, module, environment, event, duration, status, and actor when safe.
Tokens, cookies, passwords, secrets, private file content, and unnecessary
personal data are never logged.

Each API exposes an internal Prometheus-compatible `/metrics` endpoint.
Long-lived workers expose the same format on their configured
`*_WORKER_METRICS_PORT` (default `9100`) inside the Compose network. Metrics
cover request count, latency and errors; database pool state; worker duration
and failures; outbox backlog and age; SLA warnings/breaches; and
low-cardinality module operation counters.

Labels may contain service, module, worker, route template, status, operation,
outcome, and SLA metric. User IDs, object IDs, filenames, SQL, query strings,
and request bodies are forbidden labels.

OpenTelemetry configuration remains optional; a missing exporter must not stop
the application. Readiness validates dependencies, liveness remains
process-only, and `/metrics` is not a readiness probe.
