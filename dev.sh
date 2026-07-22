#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMAND="${1:-up}"
if [[ $# -gt 0 ]]; then shift; fi

case "$COMMAND" in
  up|down|restart|logs|status|reset|test|test-unit|test-integration|test-e2e|generate-contracts|architecture-check|create-module|migrate-identities) ;;
  *) printf 'Usage: ./dev.sh {up|down|restart|logs|status|reset|test|test-unit|test-integration|test-e2e|generate-contracts|architecture-check|create-module|migrate-identities} [args]\n' >&2; exit 2 ;;
esac

cd "$ROOT_DIR"

case "$COMMAND" in
  up|down|restart|logs|status|reset|test|test-integration|migrate-identities)
    command -v docker >/dev/null 2>&1 || { printf 'Docker is required for %s.\n' "$COMMAND" >&2; exit 1; }
    docker info >/dev/null 2>&1 || { printf 'Docker is not running.\n' >&2; exit 1; }
    ;;
esac

if [[ -x .venv/bin/python ]]; then
  PROM_PYTHON=.venv/bin/python
else
  PROM_PYTHON=python3
fi

case "$COMMAND" in
  up)
    if ! docker compose --profile full up --build -d --wait; then
      docker compose ps >&2
      docker compose logs --tail 200 >&2
      exit 1
    fi
    docker compose ps
    printf '\nPROM:                 http://localhost:5173/\n'
    printf 'Projects:             http://localhost:5173/projects\n'
    printf 'Service Desk:         http://localhost:5173/service-desk\n'
    printf 'Access API:           http://localhost:5173/api/access/v1/\n'
    printf 'Projects API:         http://localhost:5173/api/projects/v1/\n'
    printf 'Service Desk API:     http://localhost:5173/api/service-desk/v1/\n'
    ;;
  down) docker compose down ;;
  restart) docker compose restart "$@" ;;
  logs) docker compose logs --follow --tail 200 "$@" ;;
  status) docker compose ps ;;
  reset)
    printf 'WARNING: this removes all local PROM databases and Service Desk attachments.\n' >&2
    docker compose down --volumes
    docker compose --profile full up --build -d --wait
    ;;
  test)
    docker compose --profile test run --rm projects-tests
    docker compose --profile test run --rm service-desk-tests
    docker compose --profile test run --rm frontend-tests
    ;;
  test-unit) npm test ;;
  test-integration)
    docker compose --profile test run --rm projects-tests
    docker compose --profile test run --rm service-desk-tests
    ;;
  test-e2e) npm run test:e2e --workspace=@prom/platform-shell ;;
  generate-contracts) npm run generate:contracts ;;
  architecture-check) "$PROM_PYTHON" tools/architecture/check.py ;;
  create-module)
    [[ $# -eq 1 ]] || { printf 'Usage: ./dev.sh create-module <module-name>\n' >&2; exit 2; }
    "$PROM_PYTHON" tools/generators/create_module.py "$1"
    ;;
  migrate-identities)
    [[ $# -eq 1 && ( "$1" == "--dry-run" || "$1" == "--apply" ) ]] || {
      printf 'Usage: ./dev.sh migrate-identities {--dry-run|--apply}\n' >&2
      exit 2
    }
    docker compose --profile migration run --rm --build access-identity-migrate "$1"
    ;;
esac
