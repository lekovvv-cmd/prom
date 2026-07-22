# Secrets and production configuration

`.env.example` is a local inventory, not a production secret file. Production
values are injected at runtime from the deployment platform or secret manager
and are never committed, copied into images, printed by CI, or passed in
command-line arguments visible to other processes.

## Ownership

| Prefix | Owner | Examples |
| --- | --- | --- |
| `PLATFORM_` | platform runtime | environment, frontend origin, debug |
| `ACCESS_` | Access Service | database, RSA key, key ID, issuer/audiences |
| `PROJECTS_` | Projects | database, JWKS, storage, antivirus, pools |
| `SERVICE_DESK_` | Service Desk | database, JWKS, storage, workers |
| `SSO_` | identity integration | provider, issuer, client, callbacks |
| `OTEL_` | observability | exporter, service name, sampling |
| `S3_` | infrastructure | endpoint, bucket, credentials, region |

Each database URL uses a dedicated role and non-empty password. Production
startup fails on SQLite, default JWT material, mock SSO, debug mode, wildcard
credentialed CORS, missing issuer/audience, legacy tokens, and noop antivirus.

## Rotation

- RSA keys: publish the new `kid`, deploy verifiers, switch signing, wait past
  maximum token lifetime plus cache skew, then remove the old key.
- OIDC client secret: overlap credentials when supported; otherwise schedule a
  controlled login interruption and verify callback flow.
- Database password: rotate the role secret, roll instances, verify pools, then
  revoke the old credential.
- S3 credentials: rotate per module and verify upload, download, signed URL,
  cleanup, and orphan metrics.

After rotation, inspect logs and `/metrics` for authentication errors, database
pool failures, worker failures, and outbox age. Never log or paste a secret
while troubleshooting.

For Access, mount a generated PKCS#8 RSA private key into the container and run:

```bash
docker compose --profile full exec access-service \
  python scripts/rotate_signing_key.py \
  --kid 2026-07-primary \
  --private-key-file /run/secrets/access-signing-key.pem
```

The prior key becomes verify-only and remains in JWKS during overlap. After the
configured overlap is safely past:

```bash
docker compose --profile full exec access-service \
  python scripts/rotate_signing_key.py --retire-expired
```

Never pass private PEM material directly on the command line or put it in Git.
