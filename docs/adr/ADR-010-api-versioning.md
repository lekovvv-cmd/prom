# ADR-010: Versioned APIs with compatibility aliases

Status: superseded by the runtime simplification pass.

Gateway exposes `/api/access/v1`, `/api/projects/v1`, and
`/api/service-desk/v1`. The gateway formerly exposed `/api` and
`/service-desk-api` as temporary compatibility aliases. Those aliases were
removed after auditing the current clients; all supported browser calls use
the canonical versioned routes.

The former compatibility responses included `Deprecation`, `Sunset`, and
`Link` headers. New clients and generated contracts use canonical paths. The
gateway contains no product logic.
