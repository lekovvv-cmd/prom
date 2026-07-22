# Final dead-code and repository cleanup report

Date: 2026-07-22

## Outcome

The source tree has no statically reported unused frontend files, exports, or
dependencies and no Python dependency-ownership violations. Runtime artifacts
that had accidentally become source-controlled were removed without deleting
fixtures, migrations, worker entry points, lazy routes, or OpenAPI snapshots.

## Removed

| Item | Evidence / reason |
| --- | --- |
| `.docker-access-build.err.log`, `.docker-access-build.out.log` | Tracked local Docker build diagnostics; reproducible runtime output covered by `*.log` ignore rules. |
| 16 files under `apps/projects/backend/storage/e2e_uploads/` | Generated Playwright uploads; runtime data is covered by `apps/*/backend/storage/` in `.gitignore`. |
| `apps/projects/frontend/styles.css` | Retired 1,403-line product-wide stylesheet. |
| `apps/projects/frontend/platform-foundation.css` | Retired duplicate platform foundation layer. |
| `apps/service-desk/frontend/styles.css` | Retired 2,392-line product-wide stylesheet. |
| Shell dependency on `@prom/api-client` | `knip` proved it was not a direct shell dependency after product client ownership was corrected. |
| Legacy 771-line `ProjectService` | Replaced by command, query, membership, and recommendation application services. |

Ignored runtime coverage was extended for `.pytest-tmp-*/`; the required storage,
quarantine, log, Compose log, Playwright, cache, database, and identity-report
patterns are present in `.gitignore`.

## Static verification

| Tool | Result |
| --- | --- |
| `ruff` | Passed across SDK, Access, Projects, Service Desk, and tools. |
| `mypy` | Passed: SDK 10, Access 17, Projects 84, Service Desk 103 source files. |
| `deptry` | Passed for all four Python packages; no dependency issues. |
| `eslint` | Passed with zero warnings. |
| `prettier` | Passed for all configured frontend and tooling paths. |
| `knip` | Passed with no unused files, exports, or dependencies. |
| `npm audit --omit=dev --audit-level=high` | No known vulnerabilities. |
| `pip-audit --local --skip-editable` | No known vulnerabilities in installed third-party packages. |

## Reviewed candidates retained

- `packages/frontend/api-client/src/authTokenStorage.ts` is intentionally retained.
  It stores only a short-lived bearer in module memory; the browser session secret
  remains in an HttpOnly cookie and is never readable from JavaScript.
- Projects and Service Desk legacy-token decoders remain behind explicit
  `*_ALLOW_LEGACY_TOKENS` flags that default to `false`. They are still required by
  migration compatibility tests and cannot activate in production settings.
- CLI scripts, workers, Alembic environments, lazy frontend routes, Docker entry
  points, source fixtures, migrations, and OpenAPI snapshots were checked before
  deletion candidates were accepted. They remain because static import graphs do
  not model those runtime entry points reliably.
- User-owned untracked prompt files, spreadsheets, and `outputs/` content were not
  treated as repository dead code and were not staged.
