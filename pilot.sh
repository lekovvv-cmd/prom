#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
COMPOSE=(docker compose --project-name prom-pilot --env-file .env.pilot -f compose.yaml -f compose.pilot.yaml)

usage() {
  echo "Usage: ./pilot.sh {up|down|status|logs}"
}

if [[ ! -f .env.pilot ]]; then
  cp .env.pilot.example .env.pilot
  echo "Created .env.pilot from the safe template. Set unique passwords, hostname and key path, then run ./pilot.sh up again."
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env.pilot
set +a

case "${1:-}" in
  up)
    for variable in POSTGRES_ADMIN_PASSWORD ACCESS_DB_PASSWORD PROJECTS_DB_PASSWORD ACCESS_JWT_KEY_ID ACCESS_TOKEN_ISSUER PUBLIC_HOSTNAME; do
      if [[ -z "${!variable:-}" || "${!variable}" == CHANGE_ME ]]; then
        echo "Set a non-placeholder value for $variable in .env.pilot" >&2
        exit 1
      fi
    done
    key_file="${ACCESS_JWT_PRIVATE_KEY_HOST_FILE:-./secrets/access-jwt.pem}"
    [[ "$key_file" = /* ]] || key_file="$ROOT/$key_file"
    if [[ ! -r "$key_file" ]]; then
      echo "JWT private key is not readable: $key_file" >&2
      exit 1
    fi
    "${COMPOSE[@]}" build access-service projects-backend platform-shell
    "${COMPOSE[@]}" up -d --wait postgres
    "${COMPOSE[@]}" --profile tooling run --rm access-migrate
    "${COMPOSE[@]}" --profile tooling run --rm projects-migrate
    "${COMPOSE[@]}" --profile tooling run --rm access-seed
    "${COMPOSE[@]}" --profile tooling run --rm projects-seed
    "${COMPOSE[@]}" up -d --wait access-service projects-backend projects-worker platform-shell
    echo "PROM pilot is ready at http://127.0.0.1:${PILOT_HTTP_PORT:-5173}; configure HTTPS at the host proxy for ${PUBLIC_HOSTNAME}."
    ;;
  down)
    "${COMPOSE[@]}" down
    ;;
  status)
    "${COMPOSE[@]}" ps
    ;;
  logs)
    "${COMPOSE[@]}" logs -f --tail=200
    ;;
  *)
    usage
    exit 2
    ;;
esac
