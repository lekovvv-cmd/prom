#!/bin/sh
set -eu
key="$(openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 2>/dev/null)"
printf 'ACCESS_JWT_PRIVATE_KEY=%s\n' "$(printf '%s\n' "$key" | awk '{printf "%s\\n", $0}')"
printf 'ACCESS_JWT_KEY_ID=pilot-2026\n'
