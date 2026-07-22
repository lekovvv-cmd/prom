# Authentication and RBAC

External SSO authenticates people. Access Service owns the stable platform-user
mapping, browser sessions, module catalog, groups, roles, permissions, signing
keys, and short-lived internal tokens. Product services never issue platform
tokens and never read the Access database.

## Browser session

OIDC authorization code + PKCE, or the local-only mock code/verify flow, creates
a server-side browser session. The session secret is stored only in a
`HttpOnly`, `SameSite=Lax` cookie and is `Secure` in production. A readable CSRF
cookie must match `X-CSRF-Token` on state-changing requests. Sessions have idle
and absolute expiry, rotate secrets, carry `session_version`, are revoked on
logout/permission changes, and redirect only to validated local return paths.

The frontend probes the optional session with a 200 response, then receives a
short-lived bearer for product API calls. That bearer exists only in JavaScript
memory; neither it nor the privileged session secret is stored in `localStorage`.
Anonymous, expired, revoked, disabled, invalid-state/nonce, and open-redirect
paths fail closed. Production startup rejects mock SSO and insecure/default
configuration.

## Internal tokens and signing keys

Internal RS256 tokens contain `kid`, `jti`, `iat`, `exp`, issuer, explicit
audiences, permissions, user subject, external subject, and session version.
Product modules verify locally from cached JWKS and may use a stale key only
within the configured bounded outage window.

Access persists a key ring with exactly one active signing key plus previous
verify-only keys. Rotation publishes active + overlap keys; retirement occurs
only after token TTL, clock skew, and configured overlap. Unknown keys, wrong
issuer/audience, malformed/expired tokens, and stale JWKS beyond the outage
window are rejected. Private material is never returned by JWKS or logged.

## Authorization

Effective permissions are:

```text
direct user roles + roles from every group membership
```

Available product modules are derived from active rows in `modules` referenced
by the effective permissions. Platform-only permissions do not create false
product modules. Module registration and role mutation enforce module/permission
integrity; dangling and cross-module permissions are rejected.

Every membership or group-role mutation increments affected users'
`session_version` and records before/after audit data. Direct and group
administration require `platform.admin`, duplicate relationships are rejected,
and the final effective platform administrator cannot be removed.

Central permissions gate module operations. Object-level ownership, state
transitions, optimistic versions, privacy, and row policies remain in the module
that owns the business object.
