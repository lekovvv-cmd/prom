# PROM pilot on Oracle Cloud

This guide deploys the Projects module for a two-week test on one Oracle Cloud Ampere A1 Linux VM. Plan for at least 2 OCPU and 12 GB RAM, a persistent boot/block volume, Docker Engine and Docker Compose v2.24 or later. Use test or pseudonymized project data only; pilot login is intentionally passwordless and is not production authentication.

## DNS and HTTPS

Point `PUBLIC_HOSTNAME` to the VM. The web container binds only to `127.0.0.1:5173`; allow inbound TCP 80/443 at the Oracle security list for a host-level TLS proxy. For example, install Caddy on the VM and configure:

```caddy
prom.example.edu {
    reverse_proxy 127.0.0.1:5173
}
```

Set the matching hostname in `.env.pilot`. Caddy obtains and renews the certificate. Access cookies use `Secure`, `HttpOnly` and `SameSite=Lax`; keep the browser and API on the same HTTPS hostname.

## First start

Clone the repository and select the pilot branch:

```bash
git clone https://github.com/lekovvv-cmd/prom.git
cd prom
git switch pilot/prom
cp .env.pilot.example .env.pilot
```

Set unique database passwords, the public hostname, and a stable key id in `.env.pilot`. Generate a persistent RSA key outside Git:

```bash
mkdir -p secrets
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out secrets/access-jwt.pem
chmod 600 secrets/access-jwt.pem
```

The example points `ACCESS_JWT_PRIVATE_KEY_HOST_FILE` at that file. Keep `.env.pilot` and `secrets/` private and include them in the VM's protected backup process.

Start the pilot with one command:

```bash
bash ./pilot.sh up
```

The script validates required configuration, builds Access, Projects and the shell, waits for PostgreSQL, runs Access and Projects migrations, seeds the 12 pilot users and four sample projects, then waits for the five runtime services to become healthy. Runtime services are `postgres`, `access-service`, `projects-backend`, `projects-worker` and `platform-shell`. The Service Desk containers, database, seed and bootstrap are excluded. PostgreSQL contains separate `prom_access` and `project_showcase` databases and owners.

Open `https://$PUBLIC_HOSTNAME`. Choose one of two PROM administrators, five project managers or five employees. No password or code is used. This selector must only be exposed to the pilot audience.

## Check and operate

```bash
bash ./pilot.sh status
bash ./pilot.sh logs
```

Compose health checks and `unless-stopped` restart policies allow the five services to recover after a VM reboot. Configure Docker to start with the VM. The shell remains bound to loopback, behind the HTTPS proxy.

## Backup and restore

Back up both databases and the attachment volume before updates. Example commands (run from the repository directory):

```bash
mkdir -p backups
docker compose --project-name prom-pilot --env-file .env.pilot -f compose.yaml -f compose.pilot.yaml exec -T postgres sh -c 'PGPASSWORD="$ACCESS_DB_PASSWORD" pg_dump -U prom_access -Fc prom_access' > backups/prom_access.dump
docker compose --project-name prom-pilot --env-file .env.pilot -f compose.yaml -f compose.pilot.yaml exec -T postgres sh -c 'PGPASSWORD="$PROJECTS_DB_PASSWORD" pg_dump -U project_showcase -Fc project_showcase' > backups/project_showcase.dump
docker run --rm -v prom-pilot_projects_storage:/source:ro -v "$PWD/backups:/backup" alpine:3.22 tar czf /backup/projects_storage.tar.gz -C /source .
```

Restore into a stopped/empty pilot before starting the app. Restore the volume archive into the `prom-pilot_projects_storage` volume, then restore each database with `pg_restore --clean --if-exists -U <owner> -d <database>` from the PostgreSQL container. Keep the same JWT key and `.env.pilot` values so existing sessions and token verification remain valid. Verify `bash ./pilot.sh status`, log in, and download a previously uploaded attachment after restore.

The named `postgres_data` and `projects_storage` volumes are persistent. A normal update must never remove them:

```bash
git fetch origin
git switch pilot/prom
git pull --ff-only
bash ./pilot.sh up
```

`bash ./pilot.sh down` stops the stack and preserves data. Do not use `docker compose down -v`, remove the two volumes, or delete the VM's persistent block storage during routine deployments.

## Stop

```bash
bash ./pilot.sh down
```

This pilot account chooser is a temporary testing boundary, not a corporate identity provider. Do not expose it as production authentication or place real sensitive university/personnel data in the pilot.
