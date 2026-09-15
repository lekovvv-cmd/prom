# Local development

```powershell
.\dev.cmd up
.\dev.cmd status
.\dev.cmd test
.\dev.cmd architecture-check
```

`up` selects the `full` Compose profile and exposes only the gateway at
`http://localhost:5173`. Targeted module stacks use Compose profiles directly:

```powershell
docker compose --profile core --profile projects up --build
docker compose --profile core --profile service-desk up --build
```

## Coverage

Run coverage from the repository root after installing the locked dependencies:

```powershell
uv sync --locked --all-packages --all-extras --group dev
$env:COVERAGE_SOURCE = "apps/projects/backend"
uv run --frozen coverage run -m pytest -q apps/projects/backend/tests
uv run --frozen coverage xml
uv run --frozen coverage html
uv run --frozen coverage report

npm ci
npm run test:coverage
```

For Access, use `apps/access-service` and its `tests` directory; for Service Desk,
use `apps/service-desk/backend`. SDK coverage uses
`packages/python/platform-sdk/src` with `packages/python/platform-sdk/tests`.
Each Python run replaces the previous measurement. Reports are written to
`coverage/`; frontend reports are in `apps/platform-shell/coverage/`.

Python coverage includes branches and unexecuted source files, including CLI
scripts; only tests and Alembic migrations are excluded. Frontend coverage
includes the shell, frontend packages, and every business module, including
untested files. Declaration files and test files are excluded. CI retains
XML/HTML Python reports and HTML/LCOV/frontend summaries for 14 days. The
business-module matrix discovers future backends automatically.

The initial Python floor is 65% combined line/branch coverage. Frontend floors
are 11% lines/statements, 9% functions, and 12% branches. These are regression
floors based on the measured repository, not target quality levels. Raise them
as behavioral tests improve coverage; do not lower them to accommodate a cleanup.

Coverage complements the PostgreSQL, contract, generator, and Playwright checks;
those checks still run separately. A low initial percentage identifies missing
tests and is not a reason to exclude production code from measurement.
