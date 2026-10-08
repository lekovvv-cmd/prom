# Secrets and production configuration

`.env.example` lists local settings. Inject production values from a secret manager.
Do not commit secrets or print them in CI.

| Prefix | Owner | Values |
| --- | --- | --- |
| `PLATFORM_` | platform | environment and gateway settings |
| `ACCESS_` | Access | PostgreSQL URL, RSA signing key, key ID, issuer, audiences |
| `PROJECTS_` | Projects | PostgreSQL URL, Access JWKS, upload directory, limits |
| `SERVICE_DESK_` | Service Desk | PostgreSQL URL, Access JWKS, storage directory, workers |

Attachments use local filesystem volumes. Logs are JSON with request IDs;
Prometheus metrics are available at `/metrics`.

Production validation requires PostgreSQL credentials, secure Access signing
material, and explicit issuer and audiences. Browsers use the same-origin
Platform Shell gateway.
Demo login is disabled in production.

Set `ACCESS_JWT_PRIVATE_KEY` or mount a PEM file and set
`ACCESS_JWT_PRIVATE_KEY_FILE` for deployment. Set a matching
`ACCESS_JWT_KEY_ID`; all Access instances must use the same key and ID.
Keep private PEM material out of command lines and Git.
