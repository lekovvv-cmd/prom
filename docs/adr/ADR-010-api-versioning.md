# ADR-010: Versioned APIs with compatibility aliases

Gateway exposes `/api/access/v1`, `/api/projects/v1`, and
`/api/service-desk/v1`. Existing `/api` and `/service-desk-api` paths remain
temporary compatibility aliases during client migration.

Compatibility responses include `Deprecation: true`, a `Sunset` date of
31 January 2027, and a `Link` header pointing to the canonical versioned
surface. New clients and generated contracts use canonical paths. Removing an
alias requires access-log evidence that supported clients no longer use it,
an announced migration window, and a release note. The gateway contains no
product logic.
