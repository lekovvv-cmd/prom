# Authentication and RBAC

Access Service is not an identity provider. It maps an external subject to a
platform user and issues short-lived RS256 internal tokens with `kid`, issuer,
audiences, expiry, and permissions. Modules validate signatures through the
JWKS endpoint and do not make online authorization calls per request.

Local development uses `/auth/mock/login` and the same principal contract.
Trusted headers are disabled by default; OIDC is a disabled adapter until
issuer and client configuration are supplied. Central permissions gate module
entry; object policies stay inside each product module.

Tokens have `kid`, `jti`, `iat`, `exp`, issuer, and explicit module audiences.
Access Service persists a per-user session version. Logout or administrative
revocation increments that version; Access rejects a token whose session
version is stale. Product modules verify signatures locally from cached JWKS
and may use a stale key only within the configured stale-if-error window.
After that window authentication fails closed. Short token lifetime bounds
exposure without adding an online Access call to every product request.
