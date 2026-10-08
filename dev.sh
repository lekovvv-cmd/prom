#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMAND="${1:-up}"
if [[ $# -gt 0 ]]; then shift; fi

case "$COMMAND" in
  up|down|restart|logs|status|reset|test|test-unit|test-integration|test-e2e|generate-contracts|architecture-check|create-module) ;;
  *) printf 'Usage: ./dev.sh {up|down|restart|logs|status|reset|test|test-unit|test-integration|test-e2e|generate-contracts|architecture-check|create-module} [args]\n' >&2; exit 2 ;;
esac

cd "$ROOT_DIR"

case "$COMMAND" in
  up|down|restart|logs|status|reset|test|test-integration)
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
    if ! docker compose up -d --wait postgres; then
      docker compose ps >&2
      docker compose logs --tail 200 >&2
      exit 1
    fi
    "$PROM_PYTHON" tools/postgres/ensure_generated_databases.py
    for service in access-service projects-backend service-desk-backend platform-shell; do
      docker compose build "$service"
    done
    for job in access-migrate projects-migrate service-desk-migrate access-seed projects-seed platform-bootstrap service-desk-seed; do
      docker compose --profile tooling run --rm --no-deps "$job"
    done
    for registration in apps/*/platform/registration.json; do
      [[ -f "$registration" ]] || continue
      module="$(basename "$(dirname "$(dirname "$registration")")")"
      docker compose build "$module-backend"
      docker compose --profile tooling run --rm --no-deps "$module-migrate"
    done
    if ! docker compose up -d --wait --remove-orphans; then
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
    printf 'WARNING: this removes the shared local PROM database and attachment volumes.\n' >&2
    docker compose down --volumes --remove-orphans
    "$0" up
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
    [[ $# -ge 1 && $# -le 2 ]] || { printf 'Usage: ./dev.sh create-module <module-name> [--dry-run|--check|--remove]\n' >&2; exit 2; }
    "$PROM_PYTHON" tools/generators/create_module.py "$@"
    ;;
esac
