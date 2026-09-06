# Creating a module

```powershell
.\dev.cmd create-module documents
# or: ./dev.sh create-module documents
```

The generator creates and registers bounded backend/frontend roots, health
endpoints, OpenAPI metadata and generated contract export, a manifest and lazy
routes, query-key factory, executable health test, locked-uv Dockerfile,
package manifests, gateway route, Compose profile/database/migration service,
Access permission and JWT audience metadata, and README. Workspace globs and
the platform CI discovery checks pick up the new backend and frontend
automatically.

After generation:

1. Implement domain/application behavior; keep transport adapters thin.
2. Add business permissions in addition to the generated `.access` permission.
3. Create real Alembic migrations for domain tables and PostgreSQL regression
   tests for any DB-enforced invariants.
4. Define API contracts, frontend features, object-policy tests, audit/outbox
   behavior, and idempotency/concurrency semantics where the commands need them.
5. Run `.\dev.cmd architecture-check`, backend tests, frontend checks, contract
   generation, and the module Compose profile.

The generator deliberately does not create business entities, domain tables, or
permissions beyond the module access permission. Do not manually register the
manifest, gateway route, or Compose profile: generation owns those changes.
