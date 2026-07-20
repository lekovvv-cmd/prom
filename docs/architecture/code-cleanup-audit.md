# PROM code cleanup audit

Date opened: 2026-07-16

This ledger records evidence-backed cleanup decisions for the GIGA migration.
An analyzer finding alone is not sufficient for deletion. Each candidate is
checked against static imports, dynamic routes and manifests, CLI entrypoints,
Alembic, Docker commands, workers, public contracts, and tests.

## Classification

- `ACTIVE`: required by the current supported product.
- `GENERATED`: reproducible output whose generator is the source of truth.
- `COMPATIBILITY`: intentionally retained public compatibility surface.
- `DEPRECATED_BUT_REQUIRED`: scheduled for removal but still used.
- `DEAD`: proven unreachable and removable.
- `DUPLICATE`: a second implementation of an owned capability.
- `NEEDS_REFACTOR`: live code located behind the wrong ownership boundary.

## Ledger

| Path or capability | Class | Evidence | Decision |
| --- | --- | --- | --- |
| `apps/projects/backend` | ACTIVE | Compose service, migrations, seed, tests, OpenAPI export | Retain as the Projects backend owner. |
| `apps/service-desk/backend` | ACTIVE | Compose API and workers, migrations, seed, tests, OpenAPI export | Retain as the Service Desk backend owner. |
| `apps/access-service` | ACTIVE | Compose access API, JWKS consumer contract, seed and tests | Retain as the identity/RBAC owner. |
| `apps/platform-shell/src/app/modules/registry.ts` | ACTIVE | Shell dispatches only manifests and lazy module boundaries | Manifest type is owned by `@prom/platform-contracts`; the registry no longer knows product pages. |
| `contracts/openapi/*.json` | GENERATED | `tools/contracts/generate.mjs` and `check.mjs` reproduce and compare the files | Retain generated artifacts and fail CI when stale. |
| Projects and Service Desk route facades importing `platform-shell/src` | DUPLICATE | Product pages/entities/features/widgets now live under their product packages; architecture check, build and E2E pass | Deleted the shell-owned product implementation; retain only module manifests and route entrypoints. |
| Shell-mounted `ServiceDeskAccessProvider` | DUPLICATE | Provider now lives in `apps/service-desk/frontend/providers`; it mounts only with the Service Desk module | Deleted the shell provider and global product mount. |
| `serviceDeskCounterInvalidation` in generic shared code | DUPLICATE | Service Desk owns refresh subscriptions and contextual counters | Deleted the generic side effect; shared API client remains product-agnostic. |
| Product selectors in shell global CSS | DUPLICATE | Global CSS is 1,526 B; module CSS is owned by Projects and Service Desk and reusable primitives by `@prom/ui` | Removed product selectors from the shell and retained explicit module style entrypoints. |
| Direct `Session.commit()` calls in product services | ACTIVE | SDK UoW/outbox/audit boundaries, PostgreSQL tests and full stack regression provide evidence | Transaction ownership is explicit; service methods no longer commit individual domain operations. |
| Compatibility API prefixes documented in this audit | COMPATIBILITY | Browser and external clients still use the existing prefixes | Keep additive aliases until a separate deprecation release and contract test authorizes removal. |

## Confirmed deletions

| Removed path/coupling | Previous class | Replacement and evidence |
| --- | --- | --- |
| `apps/platform-shell/src/shared/ui/*` | DUPLICATE ownership | Moved to `packages/frontend/ui`; frontend 113 passed in 40 files, ESLint and production build pass. |
| `apps/platform-shell/src/shared/lib/typography.ts` | DUPLICATE ownership | Moved beside `PageLayout` in `@prom/ui`; the shell no longer owns the UI helper. |
| Product manifest imports from `platform-shell/src/app/modules/registry` | NEEDS_REFACTOR | Manifest type moved to `@prom/platform-contracts`; unit tests and build pass. |
| 155 `HTTPException/status` raises inside Service Desk business modules | NEEDS_REFACTOR | Replaced with transport-free typed errors and a single API Problem Details handler; Service Desk 161 passed, 1 skipped. |
| FastAPI upload/download types inside Projects and Service Desk attachment services | NEEDS_REFACTOR | API routes now adapt to SDK-owned `IncomingFile`/`FileDownload`; Projects 33 passed, 1 skipped, and Service Desk full regression pass. |
| Independent `pip install` dependency paths in three backend Dockerfiles and CI | DUPLICATE | Replaced with committed `uv.lock`, pinned uv, locked service sync and runtime-only dependency sets; three test targets were built and exercised. |
| Shell-owned Projects and Service Desk trees (`entities`, `features`, `pages`, `widgets`, product `shared`) | DUPLICATE | The exact implementations moved to `apps/projects/frontend` and `apps/service-desk/frontend`; imports, lazy manifests, unit tests and 35 E2E scenarios prove the new owners | Deleted rather than retaining a parallel legacy UI tree. |
| `docker-compose.e2e.yml` and `apps/platform-shell/scripts/run-isolated-e2e.mjs` | DEAD | Production-like `compose.yaml --profile full` is the sole E2E contour; Playwright runs it successfully | Deleted the duplicate isolated E2E topology. |
| Old Service Desk counter invalidation and contextual-counter shell widgets | DUPLICATE | Module-owned notification/counter components use the Service Desk refresh channel | Deleted the shell copies and kept product side effects out of generic packages. |

No candidate is classified `DEAD` solely from a static scan. Git history is the
recovery mechanism; no `legacy`, `old`, or backup source tree is permitted.

## Exit evidence

The completed ledger includes:

- deptry for SDK/Access/Projects/Service Desk and Knip for frontend, all green;
- architecture route/lazy-manifest checks, Alembic head migrations, Docker
  builds, Compose worker health checks and gateway contract checks;
- every listed `DEAD`/`DUPLICATE` deletion backed by unit/build/Compose/E2E
  evidence; and
- no parallel auth, transport, error, file, audit, outbox or UI primitive
  implementation remains without a named owner.
