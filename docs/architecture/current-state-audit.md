# PROM current-state audit

Date: 2026-07-16

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

## Entrypoints and public compatibility surface

- Projects API: `backend/app/main.py`, exposed behind `/api/*` and directly on
  port 8000.
- Service Desk API: `service-desk-backend/app/main.py`, exposed behind
  `/service-desk-api/*` and directly on port 8001.
- Web application: `frontend/src/app/main.tsx`, served on port 5173.
- Local orchestration: `dev.ps1`, `dev.cmd`, `dev.sh`, and
  `docker-compose.yml`.

Existing browser URLs and the two old API prefixes are compatibility contracts
during the migration. The new versioned prefixes are additive first;
compatibility aliases are removed only in a separately planned deprecation
release.

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

## Audit rules used for subsequent clean-up

Files and dependencies are removed only after repository-wide reference search
and an affected test/build gate. Git history is the recovery mechanism; no
`legacy`, `old`, or `backup` source folders are introduced. Architectural
duplication is removed at its owner boundary instead of being hidden behind a
new generic abstraction.
