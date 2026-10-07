# Secrets and production configuration

`.env.example` lists local settings. Inject production values from a secret manager.
Do not commit secrets or print them in CI.

| Prefix | Owner | Values |
| --- | --- | --- |
| `PLATFORM_` | gateway | environment, frontend origin, debug |
| `ACCESS_` | Access | PostgreSQL URL, RSA signing key, key ID, issuer, audiences |
| `PROJECTS_` | Projects | PostgreSQL URL, Access JWKS, upload directory, limits |
| `SERVICE_DESK_` | Service Desk | PostgreSQL URL, Access JWKS, storage directory, workers |

Attachments use local filesystem volumes. Logs are JSON with request IDs;
Prometheus metrics are available at `/metrics`.

Production validation requires PostgreSQL credentials, secure Access signing
material, explicit issuer and audiences, and credentialed CORS without wildcards.
Demo login is disabled in production.

## Signing key rotation

Publish the new `kid`, switch signing, wait beyond token lifetime and JWKS cache
skew, then retire the old key:

```bash
docker compose --profile full exec access-service \
  python scripts/rotate_signing_key.py \
  --kid 2026-10-primary \
  --private-key-file /run/secrets/access-signing-key.pem

docker compose --profile full exec access-service \
  python scripts/rotate_signing_key.py --retire-expired
```

Keep private PEM material out of command lines and Git.
