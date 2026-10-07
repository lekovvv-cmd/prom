# PROM platform architecture

PROM is a modular monorepo. The platform shell delivers one lazy-loaded web
application; Access Service owns platform identity mappings and RBAC; Projects
and Service Desk remain independent product services with their own databases.

```text
Demo user chooser -> Access browser session -> RBAC
                  -> short-lived internal JWT / JWKS
                  -> Projects / Service Desk
Platform shell -> gateway -> versioned module APIs
Projects / Service Desk -> separate PostgreSQL databases + local attachments
JSON logs + request IDs + Prometheus metrics
```

No product service owns global identity, and no module reads another module's
database.

