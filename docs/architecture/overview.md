# PROM platform architecture

PROM is a modular monorepo. The platform shell delivers one lazy-loaded web
application; Access Service owns platform identity mappings and RBAC; Projects
and Service Desk remain independent product services with their own databases.

```text
Demo user chooser -> Access browser session -> RBAC
                  -> short-lived internal JWT / JWKS
                  -> Projects / Service Desk
Platform shell -> gateway -> versioned module APIs
Projects / Service Desk -> separate databases in one PostgreSQL server + local attachments
JSON logs + request IDs + Prometheus metrics
```

No product service owns global identity, and no module reads another module's
database.

The local runtime has seven containers: PostgreSQL, Access, Projects API and
worker, Service Desk API and worker, and the platform shell. Migrations and demo
seeding run as temporary jobs through `dev.sh up` or `dev.cmd up`.

