# ULTIMATE completion baseline

Captured: 2026-07-22 (Asia/Yekaterinburg)

## Repository state

- Branch: `architecture/prom-platform-giga-migration`
- HEAD: `21fca5f2d67745fa413d8855af39ef6a51e6d962`
- Diff against `main`: 765 files changed, 83,771 insertions, 15,557 deletions.
- The worktree was already dirty before completion work started. Existing user-owned changes are preserved.
- Pre-existing status included deletion of `PROM_ARCHITECTURE_MIGRATION_MEGA_FINAL.md`, untracked requirement prompts, `outputs/`, and two `.xlsx` files.
- Git reported access warnings for `apps/service-desk/backend/.pytest-tmp-full/` and `.pytest-tmp-stage7/`.

## Required baseline commands

| Command | Result | Evidence |
| --- | --- | --- |
| `git status --short` | PASS with dirty tree | Pre-existing changes listed above. |
| `git branch --show-current` | PASS | `architecture/prom-platform-giga-migration` |
| `git rev-parse HEAD` | PASS | `21fca5f2d67745fa413d8855af39ef6a51e6d962` |
| `git diff --stat main...HEAD` | PASS | 765 files; +83,771 / -15,557 |
| `uv lock --check` | PASS | `uv` was not on `PATH`; ran the installed `C:\Users\anton\.local\bin\uv.exe`. Lock resolved 86 packages. |
| `npm ci` | PASS with security finding | 292 packages installed; npm reported 2 high-severity vulnerabilities. |
| `python tools/architecture/check.py` | PASS | System `python` was not on `PATH`; ran `.venv\Scripts\python.exe`. |
| `npm run check:contracts` | PASS | OpenAPI contracts current. |
| `npm run lint` | PASS | ESLint completed with zero warnings. |
| `npm run typecheck` | PASS | TypeScript project check completed. |
| `npm run test` | PASS | 40 files, 113 tests, 0 failures, 0 skips. |
| `npm run build:check` | PASS | Vite build and bundle budgets passed. Initial JS 275,723 B; initial CSS 29,053 B. |
| `docker compose config --quiet` | PASS | Compose configuration valid. |

## Baseline blockers visible before implementation

- No verified legacy identity migration rehearsal.
- Browser auth still needs a verified cookie/session and CSRF path.
- Access dynamic modules, group-derived permissions, and persisted key rotation require implementation verification.
- Projects application services and transaction ownership require verification/refactoring.
- Giant product CSS files remain (`projects` about 1,403 lines; `service-desk` about 2,392 lines).
- Clean Compose, persistence, storage rollback, and complete gateway E2E have not yet been reproduced.
- `npm ci` reports two high-severity dependency findings.

