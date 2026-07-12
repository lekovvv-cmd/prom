#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMAND="${1:-up}"
if [[ $# -gt 0 ]]; then shift; fi

case "$COMMAND" in
  up|down|restart|logs|status|reset|test) ;;
  *) printf 'Usage: ./dev.sh {up|down|restart|logs|status|reset|test} [service]\n' >&2; exit 2 ;;
esac

command -v docker >/dev/null 2>&1 || { printf 'Docker is required.\n' >&2; exit 1; }
docker info >/dev/null 2>&1 || { printf 'Docker is not running.\n' >&2; exit 1; }
cd "$ROOT_DIR"

case "$COMMAND" in
  up)
    if ! docker compose up --build -d --wait; then
      docker compose ps >&2
      docker compose logs --tail 200 >&2
      exit 1
    fi
    docker compose ps
    printf '\nPROM:                 http://localhost:5173/\n'
    printf 'Projects:             http://localhost:5173/projects\n'
    printf 'Service Desk:         http://localhost:5173/service-desk\n'
    printf 'Projects Swagger:     http://localhost:8000/docs\n'
    printf 'Service Desk Swagger: http://localhost:8001/docs\n'
    ;;
  down) docker compose down ;;
  restart) docker compose restart "$@" ;;
  logs) docker compose logs --follow --tail 200 "$@" ;;
  status) docker compose ps ;;
  reset)
    printf 'WARNING: this removes all local PROM databases and Service Desk attachments.\n' >&2
    docker compose down --volumes
    docker compose up --build -d --wait
    ;;
  test)
    docker compose --profile test run --rm projects-tests
    docker compose --profile test run --rm service-desk-tests
    docker compose --profile test run --rm frontend-tests
    ;;
esac
