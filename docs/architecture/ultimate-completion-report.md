# PROM Platform Migration ULTIMATE completion report

Date: 2026-07-22  
Branch: `architecture/prom-platform-giga-migration`

## Verdict

`READY_TO_MERGE`

All completion-prompt P0/P1 blockers are closed. The branch has not been merged
into `main`. The final SHA and user-owned dirty worktree entries are reported by
the handoff message because this report itself is the last documentation commit.

## Completion matrix

| Requirement | Result | Evidence |
| --- | --- | --- |
| Legacy identity migration | DONE | Dry-run/apply/reapply against PostgreSQL: 5 identities, 0 conflicts, 0 warnings, second apply 5 `noop`; conflict and relationship regression tests pass. |
| Access modules and RBAC | DONE | Database-derived active modules; direct + group permissions; mutation revocation; last-admin and module-integrity enforcement; PostgreSQL group test passes. |
| Signing and browser auth | DONE | Persisted active/verify-only key ring, overlap/retirement, multi-key JWKS, HttpOnly/CSRF session, safe callback/logout, idle/absolute/rotation/revocation, memory-only bearer. |
| Projects application layer | DONE | Commands, queries, membership, recommendation, responses, tasks, and reports own explicit UoW boundaries; rollback/audit/outbox/idempotency/concurrency tests pass. |
| Storage | DONE | Quarantine/finalize and checksum validation; physical delete occurs only after committed `PENDING_DELETE` + outbox; worker retry/idempotence and cleanup safety pass. |
| Frontend migration | DONE | Tailwind 4, semantic tokens, shared primitives, scoped styles, generic transport, lazy module assets, mobile/axe/E2E and bundle budgets pass. |
| Generator and CI | DONE | Real atomic roundtrip restores workspace; CI performs generated PostgreSQL migration, backend health, frontend, gateway, contracts, architecture, cleanup, security, and affected-consumer jobs. |
| Operations | DONE | Clean production-like Compose, demo isolation, rootless runtime, persistence, seed idempotence, metrics/readiness, pinned images, and restricted published ports verified. |

## Legacy identity reconciliation

The workflow reads Projects and Service Desk legacy identities, normalizes
email, preserves the existing Projects UUID as the platform UUID, stores the
external SSO subject independently, synchronizes the Service Desk projection,
assigns module roles, and writes Access audit events. Ambiguous duplicate email,
UUID, external-subject, or invalid-email plans fail before mutation.

| Identity | Preserved platform UUID | Canonical fixture role |
| --- | --- | --- |
| `admin@utmn.ru` | `00000000-0000-0000-0000-000000000001` | `platform_admin` |
| `project.manager@utmn.ru` | `00000000-0000-0000-0000-000000000002` | `project_manager` |
| `employee@utmn.ru` | `00000000-0000-0000-0000-000000000003` | `employee` |
| `sd.manager@utmn.ru` | `00000000-0000-0000-0000-000000000004` | `employee`, `service_desk_manager` |
| `sd.admin@utmn.ru` | `00000000-0000-0000-0000-000000000005` | `employee`, `service_desk_admin` |

The final rehearsal was intentionally repeated after E2E role mutations. It
still reported 5 identities, 0 conflicts, 0 warnings, and 5 no-ops. Automated
coverage proves preserved ownership of projects, responses, tasks, reports,
tickets, and the Access token subject; changed email remains bound by external
subject; disabled users remain disabled.

## Access Service evidence

Effective permissions are the union of direct user roles and all group roles.
Product modules are calculated from active database modules referenced by the
effective permission set; `platform.admin` alone does not fabricate a product
module. A temporary `documents` module and role appear without Access code
changes, while cross-module permission assignment is rejected with 422.

| Role | Projects | Service Desk | Administration |
| --- | --- | --- | --- |
| employee | view/respond | none unless separately granted | none |
| project manager | create/manage own, members, responses, tasks, reports | none unless separately granted | none |
| Service Desk manager | only if separately granted | assignee/assign/approve/priority/all tickets/reports | no configuration |
| Service Desk admin | only if separately granted | operational permissions plus catalog/SLA/access/templates/routing/approvals | Service Desk only |
| platform admin | all registered permissions | all registered permissions | platform administration |

Group member/role removal increments every affected user's `session_version`,
so stale sensitive sessions fail immediately. Tests cover direct, group, union,
removal, duplicate membership, forbidden non-admin, last administrator, and
cross-module denial.

The database key ring keeps exactly one active private key and previous public
verification keys for the configured overlap. Rotation and retirement commands
are documented; a restart preserves the active `kid`. Unknown `kid`, wrong
issuer/audience, expired/tampered tokens, stale JWKS beyond its bounded outage
window, invalid OIDC state/nonce/PKCE, and open redirects fail closed.

Browser authentication uses a server-side session secret in an HttpOnly cookie;
JavaScript receives only a short bearer kept in module memory. State changes use
the readable CSRF companion cookie plus header. Anonymous bootstrap uses a 200
session probe, avoiding expected 401 console noise without weakening protected
endpoints. Production rejects mock SSO, insecure cookies, default signing
material, legacy tokens, SQLite, and noop antivirus.

## Projects services and Unit of Work

| Component | Current source lines |
| --- | ---: |
| Former monolithic `ProjectService` | removed (771 before) |
| `ProjectServiceBase` shared helpers | 296 |
| `ProjectCommandService` | 234 |
| `ProjectQueryService` | 145 |
| `ProjectMembershipService` | 115 |
| `ProjectRecommendationService` | 233 |
| `ProjectResponseService` | 368 |
| `ProjectTaskService` | 370 |
| `ReportService` | 126 |

Repositories only read/write/flush/lock. Application use cases own the explicit
transaction boundary and atomically persist business state, audit, outbox, and
idempotency records. The suite proves total rollback after a simulated outbox
failure, durable direct invocation, stale `If-Match` 409, idempotent commands,
and two simultaneous PostgreSQL workers claiming different outbox events.
Service Desk composite ticket, approval, routing, SLA, history, notification,
and attachment paths use the same explicit UoW rule without a wholesale rewrite.

## Storage lifecycle

Uploads stream into quarantine, enforce count/size/archive/MIME rules, compute a
SHA-256 checksum, scan fail-closed, put via the local/S3 storage contract, and
finalize idempotently. A database failure after the put records or removes the
known orphan safely.

Deletion first commits `PENDING_DELETE`, audit, and
`StorageObjectDeleteRequested`; download is denied in that state. An idempotent
worker performs the physical delete, retries with backoff/dead-letter behavior,
then marks metadata deleted. Cleanup is bounded, dry-run capable, state-aware,
and does not remove live/finalizing quarantine objects. Tests cover rollback,
storage/scanner failure, duplicate finalize/delete, retry, authorization, MIME
spoofing, traversal, archive/size/count limits, signed URL TTL, and cleanup.

## Frontend and CSS metrics

| Metric | Before | After |
| --- | ---: | ---: |
| CSS files | 6 | 33 |
| Total source lines | 5,999 | 5,935 |
| Largest stylesheet | 2,392 | 274 |
| Shell global stylesheet | 91 | 86 |
| Raw colors | 254 | 169, all token/theme owned |
| `!important` | 6 | 0 |
| Unused selectors | not gated | 0 |
| Style warnings | not gated | 0 |

Production budgets passed: initial JS 273,673 B / 300,000; initial CSS
27,817 B / 30,000; largest lazy JS 46,972 B / 60,000; largest CSS
44,017 B / 45,000. The shared API client retains status, code, type,
request ID, field errors, and raw details while containing no Projects,
ticket, SLA, or report behavior.

## Generator acceptance

The real `audit-sample-module` dry-run/create/check/remove cycle created backend
package/config/health/PostgreSQL/Alembic/UoW/errors/audit-outbox/Docker/tests,
frontend manifest/lazy route/query keys/client/theme/page/test, and platform
workspace/Access/Compose/gateway/contracts/CI/docs registration. Removal restored
the exact pre-existing worktree status. Atomic failure injection and roundtrip
tests passed 2/2. CI additionally starts generated PostgreSQL, applies migration,
checks health, builds frontend, verifies contracts/gateway/architecture, and
removes the module.

## Exact verification totals

| Contour | Result |
| --- | --- |
| Platform SDK pytest | 21 passed |
| Access pytest | 39 passed, 1 PostgreSQL-only skip |
| Projects pytest | 34 passed, 1 PostgreSQL-only skip |
| Service Desk pytest | 162 passed, 1 PostgreSQL-only skip |
| Separate PostgreSQL contours | 3 passed: Access RBAC/rotation, Projects two-worker outbox, Service Desk 8-thread numbering |
| Generator tests | 2 passed |
| Frontend Vitest | 40 files, 111 passed |
| Playwright through versioned gateway | 35 passed, 0 skipped, 4.1 minutes |

The three local pytest skips are environment gates, not suppressed failures;
each skipped PostgreSQL test was rerun against its own real PostgreSQL database
and passed. `ruff`, mypy (10/17/84/103 files), deptry, ESLint, Prettier, knip,
architecture, gateway, Compose configuration, OpenAPI freshness, and bundle/style
checks pass. `pip-audit` and `npm audit --omit=dev` report no known production
vulnerabilities.

## Compose, persistence, and E2E

On new volumes, `--profile full` started with zero users/projects/tickets and no
seed dependency. All 12 long-running containers became healthy; migrations and
the four optional demo bootstrap/seed containers exited 0. APIs run as `app`,
the gateway runs as `nginx`, only port 5173 is published, database/API/metrics
ports stay internal, and worker metrics respond.

After E2E, the persistence snapshot was:

```text
users=5 | browser_sessions=43 | active_kid=local-ephemeral
projects=7 | responses=6 | tasks=0 | attachments=3 | reports=0 | outbox=4
tickets=12 | service_desk_attachments=5 | notifications=35 | notification_outbox=70
project_files=3 | service_desk_files=4
```

The snapshot was identical after restarting all three APIs and after complete
container reconstruction with volumes retained. Re-running demo bootstrap kept
the control counts exactly `5|7|48|4`, proving seed idempotence. The development
`local-ephemeral` key name is database-persisted; production validation requires
operator-provided non-default key material.

Playwright covers anonymous selector/login, employee, project manager, Service
Desk manager, Service Desk admin, platform admin, forbidden direct URLs, dynamic
role changes, logout/session revocation, project create/respond/accept, uploads
and downloads, catalog/templates/approvals/routing/SLA/workbench/ticket lifecycle,
desktop/mobile layout, automated axe checks, and clean console/network behavior.

## Remaining non-blocking limitations

- Pytest emits a Starlette `httpx` deprecation warning; migration to `httpx2`
  should follow the upstream compatibility window.
- One negative token test deliberately uses a short HMAC fixture and emits an
  `InsecureKeyLengthWarning`; production configuration rejects such secrets.
- Full `npm audit` reports a dev-only advisory in the latest
  `openapi-typescript 7.13.0` chain (`@redocly/openapi-core 1.34.17` pins
  `js-yaml 4.2.0`). It is not shipped, receives generated trusted JSON, has no
  compatible non-breaking update, and `npm audit --omit=dev` is clean. Track the
  upstream release; do not force an incompatible major override.
- The primary worktree retains the user's pre-existing deleted/untracked prompt,
  output, and spreadsheet entries. They were intentionally neither staged nor
  deleted.
