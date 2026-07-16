# ADR-007: PostgreSQL transactional outbox

Reliable asynchronous side effects are persisted with the business write and
processed by idempotent workers; no broker is introduced without a proven need.

