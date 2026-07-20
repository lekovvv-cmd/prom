# PROM current-state audit

Date: 2026-07-20

## Baseline

The repository started with three top-level applications: `backend` (Projects),
`service-desk-backend`, and `frontend`. The frontend was a single Vite build;
the two APIs owned separate PostgreSQL databases, but the Compose bootstrap
made Service Desk read the Projects database directly to copy demo identities.
That is the cross-module data dependency this migration removes.

| Measure | Baseline |
| --- | ---: |
| Projects Python files | 79 |
| Service Desk Python files | 158 |
| Frontend TypeScript/TSX files | 212 |
| Projects tests | 18 |
| Service Desk tests | 113 |
| Frontend tests | 97 |
| Declared API endpoints | 168 |
| Existing production asset size | 624,575 bytes |
| Compose services | 13 |

The Projects unit suite passed locally (`18 passed`). The complete Service Desk
suite did not complete within the local 60-second command limit, so it is not
recorded as a passing baseline. It remains a required regression gate after
the structural migration.

## GIGA continuation baseline

The GIGA migration starts from the MEGA migration snapshot on
`architecture/prom-platform-giga-migration`. The product is runnable, but the
snapshot is not yet compliant with the stronger GIGA production gates.

| Measure | GIGA start |
| --- | ---: |
| Projects Python files | 79 |
| Service Desk Python files | 159 |
| Access Service Python files | 17 |
| Frontend TypeScript/TSX files | 221 |
| Frontend CSS files | 1 |
| Projects test files | 2 |
| Service Desk test files | 28 |
| Access Service test files | 1 |
| Frontend unit test files | 38 |
| Global CSS lines | 5,122 |
| Module selectors in global CSS | 294 |
| Direct database commit call sites | 30+ |

The following are confirmed gaps, not inferred future risks:

1. There was no committed Python lockfile, and the three backend Dockerfiles
   installed dependencies with `pip` independently of CI.
2. `apps/projects/frontend` and `apps/service-desk/frontend` imported their
   pages, providers, widgets, and UI directly from `apps/platform-shell/src`.
   The packages were route facades rather than independent product modules.
3. Product-specific selectors remained in the only global stylesheet, so the
   shell still owned the visual implementation of both products.
4. Projects kept a 592-line application service with transaction commits mixed
   into business operations and no explicit unit-of-work boundary.
5. Access Service had no real migration history and its OIDC adapter remained a
   disabled stub.
6. The architecture checker did not inspect the actual backend package layout,
   so transport and transaction boundary violations could pass CI.

This section is the measurement point for the GIGA delta. The final gate table
below is the authoritative completion record for this branch.

### Final GIGA verification

| Gate | Result |
| --- | --- |
| `uv lock --check` | current 86-package workspace lock verified on Python 3.14.6 |
| Ruff / dependency ownership | Ruff passed; deptry passed for SDK (10 files), Access (14), Projects (80), and Service Desk (103) |
| MyPy | SDK 10, Access 14, Projects 76, Service Desk 96 source files — all clean |
| Backend and SDK regressions | SDK 13 passed; Access 13 passed; Projects 33 passed, 1 skipped; Service Desk 161 passed, 1 skipped |
| Frontend unit tests | 113 passed in 40 files |
| Frontend quality | Prettier, ESLint, TypeScript, CSS ownership check and Knip passed |
| Frontend production build | initial JS 275,723 B / CSS 29,053 B; largest lazy JS 46,972 B / CSS 36,079 B — all within budgets |
| Architecture checker | passed |
| Gateway, Compose, contracts | gateway, `docker compose config --quiet`, and OpenAPI generated-contract checks passed |
| Production-like full stack | clean-volume Compose healthy; migrations/bootstrap/seed containers exited 0; 35/35 serial Chromium E2E passed |
| Security | npm audit, Linux `pip-audit`, repository Trivy and all four runtime-image Trivy scans passed with zero CRITICAL findings |

The PostgreSQL migration, concurrency, outbox and SLA integration gates were
also run during the migration. The final clean-volume Compose run confirms that
the resulting image set starts, migrates, seeds, exposes health/metrics, and
serves both product modules together.

## Entrypoints and public compatibility surface

- Access API: `apps/access-service/src/access_service/bootstrap/app.py`,
  canonical gateway prefix `/api/access/v1`.
- Projects API: `apps/projects/backend/app/main.py`, canonical gateway prefix
  `/api/projects/v1`.
- Service Desk API: `apps/service-desk/backend/app/main.py`, canonical gateway
  prefix `/api/service-desk/v1`.
- Web application: `apps/platform-shell/src/app/main.tsx`, served by the
  gateway on port 5173 and dispatching product manifests lazily.
- Local orchestration: `compose.yaml`, `dev.ps1`, `dev.cmd`, and `dev.sh`.

The gateway owns versioned public paths, security headers, request size/time
limits, health routing and compatibility aliases. Browser paths remain stable;
internal backend ports are not the public integration surface.

## Confirmed architectural findings

1. `service-desk-backend/scripts/bootstrap_identity.py` connects directly to
   the Projects DB and copies user records. This violates module data
   ownership and is replaced by Access Service demo-user seeding.
2. `frontend/src/shared/api/client.ts` embeds Service Desk counter
   invalidation in the generic client. The generic transport must not know
   module side effects.
3. `frontend/src/app/routes/AppRouter.tsx` imports all Projects and Service
   Desk pages eagerly. Module manifests and lazy route loading replace this
   coupling.
4. `frontend/src/app/providers/AppProviders.tsx` mounts the Service Desk
   provider globally. That provider belongs inside the Service Desk module.
5. Docker production images install test/dev dependencies. The new images use
   runtime-only dependency installation once the workspace lockfile is in
   place.

The lockfile gap is addressed by the root `uv.lock`; Docker and CI consume it
in locked/frozen mode. Runtime images sync only their selected service without
its `dev` extra. Python 3.14.6, Node 24.13.1 and the Nginx runtime image are
version-and-digest pinned. The clean image, Compose and security gates are now
complete.

## Audit rules used for subsequent clean-up

Files and dependencies are removed only after repository-wide reference search
and an affected test/build gate. Git history is the recovery mechanism; no
`legacy`, `old`, or `backup` source folders are introduced. Architectural
duplication is removed at its owner boundary instead of being hidden behind a
new generic abstraction.
