# PROM platform workspace

PROM is a modular university platform with a shared shell and three backend services:

- `apps/access-service` — demo login, browser sessions, JWT/JWKS and central RBAC;
- `apps/projects/backend` — Projects domain and its own PostgreSQL database;
- `apps/service-desk/backend` — Service Desk domain and its own PostgreSQL database;
- `apps/platform-shell` — React platform shell; product routes are lazy-loaded from module manifests;
- `packages/python/platform-sdk` — infrastructure-only Python helpers.

One PostgreSQL server hosts three separately owned databases: `prom_access`, `project_showcase`, and `service_desk`. Services never access one another's databases. Browser traffic goes through the platform-shell gateway.

## Start locally

Docker Desktop is the only required runtime.

```powershell
.\dev.cmd up
```

or:

```bash
./dev.sh up
```

`up` starts PostgreSQL, applies migrations and demo fixtures with temporary containers, then starts the seven runtime containers. Open `http://localhost:5173/`. Repeating `up` preserves existing demo data.

| Surface | URL |
| --- | --- |
| Platform shell | `http://localhost:5173/` |
| Access API | `http://localhost:5173/api/access/v1/` |
| Projects API | `http://localhost:5173/api/projects/v1/` |
| Service Desk API | `http://localhost:5173/api/service-desk/v1/` |

The runtime containers are `postgres`, `access-service`, `projects-backend`, `projects-worker`, `service-desk-backend`, `service-desk-worker`, and `platform-shell`. The `tooling` and `test` Compose profiles contain temporary jobs only.

## Common commands

```powershell
.\dev.cmd status
.\dev.cmd logs access-service
.\dev.cmd test
.\dev.cmd test-unit
.\dev.cmd generate-contracts
.\dev.cmd architecture-check
.\dev.cmd create-module example-module
```

`reset` removes the local shared PostgreSQL and attachment volumes and brings back a ready demo. `down` preserves them.

```powershell
.\dev.cmd reset
```

For host-side tooling, use Python 3.14 and Node 24:

```powershell
npm.cmd ci
npm.cmd run test
npm.cmd run build
npm.cmd run check:contracts
```

OpenAPI snapshots are committed in `contracts/openapi/`; regenerate them after an API change with `npm run generate:contracts`. The CI contract job rejects stale snapshots.

## Demo identities

After `up`, the development Access Service
accepts code `000000` for the seeded accounts: `employee@utmn.ru`,
`project.manager@utmn.ru`, `sd.manager@utmn.ru`, `sd.admin@utmn.ru`, and
`admin@utmn.ru`. The backend verifies this code and creates the same browser
session used by the platform. Demo login is available only outside production.
Legacy identity reconciliation is a separate migration tool for existing databases.

For existing Projects or Service Desk databases, inspect the reconciliation report
before applying it:

```powershell
.\dev.cmd migrate-identities --dry-run
.\dev.cmd migrate-identities --apply
```

Reports are written to `outputs/identity-migration/`. An empty source database
produces `identities: 0` and an explicit warning; it does not create demo users.

## Production configuration

Copy `.env.example` only as a local inventory; inject production values from a
secret manager. Production startup rejects default signing material, empty
PostgreSQL passwords, debug mode, and missing
issuer/audience values.

The primary prefixes are `PLATFORM_`, `ACCESS_`, `PROJECTS_`,
and `SERVICE_DESK_`. Attachments use local filesystem volumes. See
[secrets and configuration](docs/operations/secrets.md) and
[deployment](docs/operations/deployment.md).

## Documentation

Architecture, module boundaries and operational instructions are in [docs/architecture](docs/architecture/overview.md), [docs/development](docs/development/local-development.md), and [docs/operations](docs/operations/deployment.md). Architectural decisions are recorded in `docs/adr/`.
