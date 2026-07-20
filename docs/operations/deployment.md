# Deployment

Compose is for local and test environments. Production deploys immutable
images tagged by commit SHA, separate service/database credentials, non-root
runtimes, readiness and liveness probes, and measured resource limits. Seed
data is never an automatic production-startup step.

## Release order

1. Build and scan Access, Projects, Service Desk, and platform-shell images.
2. Back up the affected database and confirm the restore checkpoint.
3. Apply additive migrations for Access, then selected product modules.
4. Deploy APIs and workers with readiness gating.
5. Deploy the gateway/platform shell last.
6. Verify canonical health routes, `/metrics`, login, one read flow, one write
   flow, outbox age, and worker failures.

Projects, Service Desk, and Access can be released independently while
published contracts remain compatible. A shared SDK change rebuilds and tests
all dependent images.

## Zero-downtime migrations

Use expand/contract:

1. add nullable columns, new tables, or compatible indexes;
2. deploy code that can read old and new shapes;
3. backfill in bounded, restartable batches;
4. switch writes and verify metrics;
5. make constraints strict only after validation;
6. remove old shapes in a later release.

Do not combine destructive contraction with the first code release that stops
using the old shape.

## Rollback and forward-fix

Application rollback is safe only while the previous image understands the
expanded schema. Database downgrade is not the default incident response:
prefer a forward-fix once writes occurred after upgrade. Before any downgrade,
stop writers, capture a fresh backup, inspect the Alembic downgrade, and prove
that it does not discard production data.

If readiness fails, keep the old replica serving traffic, collect logs and
migration status, and never run seed, reset, or volume-deletion commands.
