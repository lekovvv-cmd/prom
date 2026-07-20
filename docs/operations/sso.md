# SSO operation

Set `SSO_PROVIDER=oidc` only after providing issuer, client ID, secret,
redirect URI, scopes, allowed audiences, and post-logout URI. Do not invent
TюмГУ endpoints. Local environments use `SSO_PROVIDER=mock`; production
configuration validation rejects mock identity and absent signing material.

## Production cutover

1. Register the exact callback and post-logout URLs with the identity team.
2. Store the OIDC client secret and Access RSA key in the secret manager.
3. Confirm discovery issuer equality, JWKS reachability, audiences, nonce
   validation, PKCE, and clock synchronization.
4. Start with a restricted pilot group and verify Access audit events.
5. Keep the mock provider disabled in every production replica.

## Outage and revocation

Product modules cache Access JWKS for the configured TTL and may use a stale
key only within `*_ACCESS_JWKS_STALE_IF_ERROR_SECONDS`. Existing valid tokens
continue until expiry; login, logout, and centralized session-version checks
require Access Service.

If key compromise is suspected, rotate the RSA key and `kid`, increment
affected session versions, shorten the stale-key window, and restart product
services if immediate cache eviction is required. Never accept trusted
identity headers from the public network; trusted-header mode requires an
explicit proxy CIDR allow-list.
