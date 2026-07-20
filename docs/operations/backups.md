# Backups and recovery

Back up each module database independently. Access, Projects, and Service Desk
have separate schedules, credentials, retention, encryption keys, and restore
evidence. Back up object storage by module prefix with the matching database
checkpoint.

## Backup checklist

- record image SHA, Alembic head, PostgreSQL version, UTC timestamp, and module;
- use a least-privileged backup identity;
- encrypt in transit and at rest;
- keep a copy outside the primary failure domain;
- verify dump size and checksum;
- alert on missing or unusually small backups;
- never include `.env` files or plaintext secret exports.

## Restore drill

1. Provision isolated PostgreSQL and private object storage.
2. Restore the database without application writers.
3. Restore module objects and compare metadata keys/checksums.
4. Run `alembic current`, then forward migrations for the target image.
5. Verify readiness, attachment authorization, outbox backlog, and
   representative read/write scenarios.
6. Record recovery time and manual steps.

A backup is valid only after a successful restore drill. Quarantined or
rejected objects must not become available during restore. Never use
`docker compose down --volumes`, `reset`, schema recreation, or demo seeds as
a production recovery method.
