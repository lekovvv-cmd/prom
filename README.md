# PROM platform workspace

PROM is a modular university platform with a shared shell and three independently deployable backend services:

- `apps/access-service` — authentication, SSO adapters, JWT/JWKS and central RBAC;
- `apps/projects/backend` — Projects domain and its PostgreSQL database;
- `apps/service-desk/backend` — Service Desk domain and its separate PostgreSQL database;
- `apps/platform-shell` — React platform shell; product routes are lazy-loaded from module manifests;
- `packages/python/platform-sdk` — infrastructure-only Python helpers.

Services never access one another's databases. Browser traffic goes only through the platform-shell gateway.

## Start locally

Docker Desktop is the only required runtime.

```powershell
.\dev.cmd up
```

or:

```bash
./dev.sh up
```

The full profile starts databases, migrations, seeds, workers and the gateway. Open `http://localhost:5173/`.

| Surface | URL |
| --- | --- |
| Platform shell | `http://localhost:5173/` |
| Access API | `http://localhost:5173/api/access/v1/` |
| Projects API | `http://localhost:5173/api/projects/v1/` |
| Service Desk API | `http://localhost:5173/api/service-desk/v1/` |

The previous `/api/` and `/service-desk-api/` gateway paths remain compatibility aliases during migration.

## Compose profiles

| Profile | Contents |
| --- | --- |
| `core` | gateway/platform shell, Access Service, Access PostgreSQL, local SSO mock |
| `projects` | Projects PostgreSQL, migrations, seed, API and workers |
| `service-desk` | Service Desk PostgreSQL, migrations, seed, API and workers |
| `full` | complete local platform |
| `test` | isolated backend and frontend test images |

```powershell
docker compose --profile core --profile projects up --build
docker compose --profile core --profile service-desk up --build
docker compose --profile full up --build
```

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

`reset` intentionally removes the local PostgreSQL volumes and uploaded files. `down` preserves them.

For host-side tooling, use Python 3.14 and Node 24:

```powershell
npm.cmd ci
npm.cmd run test
npm.cmd run build
npm.cmd run check:contracts
```

OpenAPI snapshots are committed in `contracts/openapi/`; regenerate them after an API change with `npm run generate:contracts`. The CI contract job rejects stale snapshots.

## Local mock identities

The development Access Service accepts code `000000` for the seeded accounts: `employee@utmn.ru`, `project.manager@utmn.ru`, `sd.manager@utmn.ru`, `sd.admin@utmn.ru`, and `admin@utmn.ru`. This mock provider is blocked by the production configuration guard; production must use an OIDC adapter and real key material.

## Production configuration

Copy `.env.example` only as a local inventory; inject production values from a
secret manager. Production startup rejects default signing material, empty
PostgreSQL passwords, mock SSO, debug mode, wildcard credentialed CORS,
missing issuer/audience values, legacy tokens, and disabled antivirus scanning.

The primary prefixes are `PLATFORM_`, `ACCESS_`, `PROJECTS_`,
`SERVICE_DESK_`, `SSO_`, `OTEL_`, and `S3_`. See
[secrets and configuration](docs/operations/secrets.md),
[deployment](docs/operations/deployment.md), and
[SSO operation](docs/operations/sso.md).

## Documentation

Architecture, module boundaries and operational instructions are in [docs/architecture](docs/architecture/overview.md), [docs/development](docs/development/local-development.md), and [docs/operations](docs/operations/deployment.md). Architectural decisions are recorded in `docs/adr/`.
