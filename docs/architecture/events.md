# Events and workers

Business writes record outbox events in the same transaction. Workers use
bounded batches, retries with backoff, idempotent consumer behavior, and
`FOR UPDATE SKIP LOCKED` when polling concurrently. Service Desk runs distinct
SLA and notification-outbox worker processes. Kafka is intentionally not a
dependency at this stage.

