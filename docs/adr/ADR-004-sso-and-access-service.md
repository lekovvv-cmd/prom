# ADR-004: External SSO and Access Service

Status: Superseded on 2026-10-07. The current demo-only login and internal
JWT/JWKS flow are documented in [Authentication and RBAC](../architecture/auth-and-rbac.md).

External SSO authenticates people. Access Service owns PROM user mapping and
issues short-lived signed internal tokens. Projects must not issue platform JWTs.

Browser clients use an Access-owned server-side session with an HttpOnly cookie,
CSRF companion token, idle/absolute expiry, rotation, and revocation. OIDC code +
PKCE and the development-only mock verifier terminate in the same session model.
The frontend may exchange a valid browser session for a short bearer kept only in
memory; privileged credentials are never persisted in browser storage.

Current signing uses one RSA key supplied from a secret or file mount in
production. Access publishes its public key through JWKS for local product
verification. The historical key ring described by this superseded ADR has
been removed.
