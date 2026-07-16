# SSO operation

Set `SSO_PROVIDER=oidc` only after providing issuer, client ID, secret,
redirect URI, scopes, allowed audiences, and post-logout URI. Do not invent
TюмГУ endpoints. Local environments use `SSO_PROVIDER=mock`; production
configuration validation rejects mock identity and absent signing material.

