# PROM platform architecture

PROM is a modular monorepo. The platform shell delivers one lazy-loaded web
application; Access Service owns platform identity mappings and RBAC; Projects
and Service Desk remain independent product services with their own databases.

```text
SSO or local mock -> Access Service -> short-lived signed platform token
                                  -> Projects / Service Desk
Platform shell -> gateway -> versioned module APIs
```

No product service owns global identity, and no module reads another module's
database.

