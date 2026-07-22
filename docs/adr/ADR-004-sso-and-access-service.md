# ADR-004: External SSO and Access Service

External SSO authenticates people. Access Service owns PROM user mapping and
issues short-lived signed internal tokens. Projects must not issue platform JWTs.

Browser clients use an Access-owned server-side session with an HttpOnly cookie,
CSRF companion token, idle/absolute expiry, rotation, and revocation. OIDC code +
PKCE and the development-only mock verifier terminate in the same session model.
The frontend may exchange a valid browser session for a short bearer kept only in
memory; privileged credentials are never persisted in browser storage.

Signing uses a database-persisted key ring with one active key and previous
verify-only keys. Rotation overlaps public keys for token TTL + skew + the
configured safety period, and production supplies private material from a secret
or file mount. This avoids login dependence on Access for every product request
while preserving restart stability and bounded fail-closed JWKS caching.
