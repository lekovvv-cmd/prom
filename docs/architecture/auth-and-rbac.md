# Authentication and RBAC

Access Service is not an identity provider. It maps an external subject to a
platform user and issues short-lived RS256 internal tokens with `kid`, issuer,
audiences, expiry, and permissions. Modules validate signatures through the
JWKS endpoint and do not make online authorization calls per request.

Local development uses `/auth/mock/login` and the same principal contract.
Trusted headers are disabled by default; OIDC is a disabled adapter until
issuer and client configuration are supplied. Central permissions gate module
entry; object policies stay inside each product module.

