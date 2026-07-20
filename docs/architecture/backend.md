# Backend conventions

Each backend keeps delivery, application, domain, infrastructure, and bootstrap
responsibilities separate. Domain code does not import FastAPI or SQLAlchemy.
One command use case defines one transaction boundary; repositories flush but
do not commit business transactions. New critical writes require idempotency,
audit/outbox recording, and optimistic concurrency when administrators can edit
the same entity.

The platform SDK contains only shared infrastructure primitives: auth, Problem
Details errors, request context/logging, storage port, and health/outbox helpers.

All maintained Python service source trees are checked by `mypy` in CI:
`platform-sdk/src`, Access Service `src`, Projects `app`, and Service Desk
`app`. Type-checking a hand-picked infrastructure subset is not an accepted
quality gate.
