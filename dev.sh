#!/usr/bin/env bash
set -Eeuo pipefail

SKIP_INSTALL=0
NO_DOCKER=0
EXIT_AFTER_READY=0
BACKEND_PORT=8000
SERVICE_DESK_PORT=8001
FRONTEND_PORT=5173

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
SERVICE_DESK_DIR="$ROOT_DIR/service-desk-backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
COMPOSE_PROJECT="shpiu_project_showcase"

BACKEND_PID=""
SERVICE_DESK_PID=""
FRONTEND_PID=""
BACKEND_PYTHON=""

log() {
  printf '[dev] %s\n' "$1"
}

fail() {
  printf '[dev] ERROR: %s\n' "$1" >&2
  exit 1
}

usage() {
  cat <<'EOF'
Usage: ./dev.sh [options]

Options:
  --skip-install, -SkipInstall      Do not install backend/frontend dependencies
  --no-docker, -NoDocker            Do not start PostgreSQL via Docker Compose
  --exit-after-ready, -ExitAfterReady
                                    Stop after backend/frontend readiness checks
  --backend-port PORT               Backend port, default 8000
  --backend-port=PORT               Same as --backend-port PORT
  --service-desk-port PORT          Service Desk backend port, default 8001
  --service-desk-port=PORT          Same as --service-desk-port PORT
  --frontend-port PORT              Frontend port, default 5173
  --frontend-port=PORT              Same as --frontend-port PORT
  -h, --help                        Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-install|-SkipInstall)
      SKIP_INSTALL=1
      shift
      ;;
    --no-docker|-NoDocker)
      NO_DOCKER=1
      shift
      ;;
    --exit-after-ready|-ExitAfterReady)
      EXIT_AFTER_READY=1
      shift
      ;;
    --backend-port|-BackendPort)
      [[ $# -ge 2 ]] || fail "$1 requires a value"
      BACKEND_PORT="$2"
      shift 2
      ;;
    --backend-port=*)
      BACKEND_PORT="${1#*=}"
      shift
      ;;
    --service-desk-port|-ServiceDeskPort)
      [[ $# -ge 2 ]] || fail "$1 requires a value"
      SERVICE_DESK_PORT="$2"
      shift 2
      ;;
    --service-desk-port=*)
      SERVICE_DESK_PORT="${1#*=}"
      shift
      ;;
    --frontend-port|-FrontendPort)
      [[ $# -ge 2 ]] || fail "$1 requires a value"
      FRONTEND_PORT="$2"
      shift 2
      ;;
    --frontend-port=*)
      FRONTEND_PORT="${1#*=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown option: $1"
      ;;
  esac
done

require_command() {
  local name="$1"
  local hint="$2"
  command -v "$name" >/dev/null 2>&1 || fail "$name is not installed or not in PATH. $hint"
}

copy_env_if_missing() {
  local dir="$1"
  if [[ ! -f "$dir/.env" ]]; then
    cp "$dir/.env.example" "$dir/.env"
    log "Created $dir/.env"
  fi
}

env_file_value() {
  local file="$1"
  local name="$2"
  [[ -f "$file" ]] || return 0
  awk -F= -v key="$name" '$1 == key { sub(/^[^=]*=/, ""); print; exit }' "$file"
}

python_is_314() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)' >/dev/null 2>&1
}

ensure_python_314() {
  local python_path="$1"
  if ! python_is_314 "$python_path"; then
    fail "$python_path exists, but it is not Python 3.14+. Remove the venv and rerun ./dev.sh."
  fi
}

find_python_314() {
  local candidate
  for candidate in python3.14 python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && python_is_314 "$candidate"; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

ensure_backend_venv() {
  local default_venv="$BACKEND_DIR/.venv"
  local linux_venv="$BACKEND_DIR/.venv-linux"
  local py314_venv="$BACKEND_DIR/.venv-py314"
  local venv_dir="$default_venv"

  if [[ -x "$default_venv/bin/python" ]]; then
    BACKEND_PYTHON="$default_venv/bin/python"
    if python_is_314 "$BACKEND_PYTHON"; then
      return
    fi
    log "Existing $default_venv is not Python 3.14+, using $py314_venv"
    venv_dir="$py314_venv"
  fi

  if [[ -d "$default_venv" && ! -x "$default_venv/bin/python" ]]; then
    venv_dir="$linux_venv"
  fi

  BACKEND_PYTHON="$venv_dir/bin/python"
  if [[ -x "$BACKEND_PYTHON" ]]; then
    ensure_python_314 "$BACKEND_PYTHON"
    return
  fi

  local python_cmd
  python_cmd="$(find_python_314)" || fail "Python 3.14 is required. Install python3.14 and try again."

  log "Creating backend virtualenv at $venv_dir"
  (cd "$BACKEND_DIR" && "$python_cmd" -m venv "$venv_dir")

  [[ -x "$BACKEND_PYTHON" ]] || fail "Could not create backend virtualenv"
}

ensure_backend_dependencies() {
  [[ "$SKIP_INSTALL" == "1" ]] && return

  if "$BACKEND_PYTHON" -c 'import importlib.util
required = ("alembic", "fastapi", "psycopg", "pydantic", "sqlalchemy", "uvicorn")
has_required = all(importlib.util.find_spec(module) for module in required)
has_multipart = any(importlib.util.find_spec(module) for module in ("python_multipart", "multipart"))
raise SystemExit(0 if has_required and has_multipart else 1)' >/dev/null 2>&1; then
    log "Backend dependencies already installed"
    return
  fi

  log "Installing backend dependencies"
  (cd "$BACKEND_DIR" && "$BACKEND_PYTHON" -m pip install --upgrade pip)
  (cd "$BACKEND_DIR" && "$BACKEND_PYTHON" -m pip install -e '.[dev]')
}

ensure_service_desk_dependencies() {
  [[ "$SKIP_INSTALL" == "1" ]] && return

  if "$BACKEND_PYTHON" -c 'import importlib.util
required = ("alembic", "fastapi", "psycopg", "pydantic", "sqlalchemy", "uvicorn")
raise SystemExit(0 if all(importlib.util.find_spec(module) for module in required) else 1)' >/dev/null 2>&1; then
    log "Service Desk backend dependencies already installed"
    return
  fi

  log "Installing Service Desk backend dependencies"
  (cd "$SERVICE_DESK_DIR" && "$BACKEND_PYTHON" -m pip install -e '.[dev]')
}

ensure_frontend_dependencies() {
  [[ "$SKIP_INSTALL" == "1" ]] && return

  if [[ -d "$FRONTEND_DIR/node_modules" ]]; then
    log "Frontend dependencies already installed"
    return
  fi

  log "Installing frontend dependencies"
  (cd "$FRONTEND_DIR" && npm install)
}

docker_compose() {
  docker compose -p "$COMPOSE_PROJECT" "$@"
}

wait_database() {
  [[ "$NO_DOCKER" == "1" ]] && return

  log "Waiting for PostgreSQL"
  for _ in $(seq 1 60); do
    if docker_compose exec -T db pg_isready -U project_showcase -d project_showcase >/dev/null 2>&1; then
      return
    fi
    sleep 1
  done

  fail "PostgreSQL did not become ready in time. Check: docker compose -p $COMPOSE_PROJECT logs db"
}

wait_service_desk_database() {
  [[ "$NO_DOCKER" == "1" ]] && return

  log "Waiting for Service Desk PostgreSQL"
  for _ in $(seq 1 60); do
    if docker_compose exec -T service_desk_db pg_isready -U service_desk -d service_desk >/dev/null 2>&1; then
      return
    fi
    sleep 1
  done

  fail "Service Desk PostgreSQL did not become ready in time. Check: docker compose -p $COMPOSE_PROJECT logs service_desk_db"
}

port_is_open() {
  "$BACKEND_PYTHON" - "$1" <<'PY'
import socket
import sys

sock = socket.socket()
sock.settimeout(0.3)
try:
    raise SystemExit(0 if sock.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
finally:
    sock.close()
PY
}

assert_port_free() {
  local port="$1"
  local name="$2"
  if port_is_open "$port"; then
    fail "$name port $port is already in use. Stop the old process or run ./dev.sh with another port."
  fi
}

wait_url() {
  local url="$1"
  local name="$2"
  local pid="$3"

  log "Waiting for $name at $url"
  for _ in $(seq 1 90); do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      fail "$name exited before becoming ready"
    fi

    if curl --fail --silent --show-error --max-time 2 "$url" >/dev/null 2>&1; then
      return
    fi
    sleep 1
  done

  fail "$name did not become ready in time"
}

cleanup() {
  trap - EXIT INT TERM

  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    log "Stopping frontend"
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
  fi

  if [[ -n "$SERVICE_DESK_PID" ]] && kill -0 "$SERVICE_DESK_PID" >/dev/null 2>&1; then
    log "Stopping Service Desk backend"
    kill "$SERVICE_DESK_PID" >/dev/null 2>&1 || true
  fi

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    log "Stopping backend"
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi

  [[ -n "$FRONTEND_PID" ]] && wait "$FRONTEND_PID" 2>/dev/null || true
  [[ -n "$SERVICE_DESK_PID" ]] && wait "$SERVICE_DESK_PID" 2>/dev/null || true
  [[ -n "$BACKEND_PID" ]] && wait "$BACKEND_PID" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

if [[ "$NO_DOCKER" != "1" ]]; then
  require_command docker "Install Docker and make sure the daemon is running."
fi
require_command npm "Install Node.js LTS/current first."
require_command node "Install Node.js LTS/current first."
require_command curl "Install curl first."

copy_env_if_missing "$BACKEND_DIR"
copy_env_if_missing "$SERVICE_DESK_DIR"
copy_env_if_missing "$FRONTEND_DIR"

ensure_backend_venv
ensure_backend_dependencies
ensure_service_desk_dependencies
ensure_frontend_dependencies

if [[ "$NO_DOCKER" != "1" ]]; then
  log "Starting PostgreSQL"
  (cd "$ROOT_DIR" && docker_compose up -d db service_desk_db)
  wait_database
  wait_service_desk_database
fi

log "Applying migrations"
(cd "$BACKEND_DIR" && "$BACKEND_PYTHON" -m alembic upgrade head)
(cd "$BACKEND_DIR" && "$BACKEND_PYTHON" scripts/seed.py)

log "Applying Service Desk migrations"
(cd "$SERVICE_DESK_DIR" && "$BACKEND_PYTHON" -m alembic upgrade head)
log "Seeding Service Desk demo data"
IDENTITY_DATABASE_URL="$(env_file_value "$BACKEND_DIR/.env" "DATABASE_URL")"
(cd "$SERVICE_DESK_DIR" && SERVICE_DESK_IDENTITY_DATABASE_URL="$IDENTITY_DATABASE_URL" "$BACKEND_PYTHON" scripts/seed.py)

assert_port_free "$BACKEND_PORT" "Backend"
assert_port_free "$SERVICE_DESK_PORT" "Service Desk backend"
assert_port_free "$FRONTEND_PORT" "Frontend"

log "Starting backend"
(cd "$BACKEND_DIR" && "$BACKEND_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT") &
BACKEND_PID=$!
wait_url "http://127.0.0.1:$BACKEND_PORT/api/health" "backend" "$BACKEND_PID"

log "Starting Service Desk backend"
(cd "$SERVICE_DESK_DIR" && "$BACKEND_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port "$SERVICE_DESK_PORT") &
SERVICE_DESK_PID=$!
wait_url "http://127.0.0.1:$SERVICE_DESK_PORT/health/live" "Service Desk backend" "$SERVICE_DESK_PID"

log "Starting frontend"
VITE_BIN="$FRONTEND_DIR/node_modules/vite/bin/vite.js"
[[ -f "$VITE_BIN" ]] || fail "Vite is not installed. Run ./dev.sh without --skip-install first."
(cd "$FRONTEND_DIR" && VITE_SERVICE_DESK_API_BASE_URL="http://localhost:$SERVICE_DESK_PORT" node "$VITE_BIN" --host 127.0.0.1 --port "$FRONTEND_PORT" --strictPort) &
FRONTEND_PID=$!
wait_url "http://127.0.0.1:$FRONTEND_PORT" "frontend" "$FRONTEND_PID"

cat <<EOF

Application is running:
  UI:                   http://localhost:$FRONTEND_PORT
  Projects Swagger:     http://localhost:$BACKEND_PORT/docs
  Service Desk Swagger: http://localhost:$SERVICE_DESK_PORT/docs

Demo users:
  admin@utmn.ru
  manager@utmn.ru
  employee@utmn.ru
  code: 000000

Press Ctrl+C to stop backend and frontend.
EOF

if [[ "$EXIT_AFTER_READY" == "1" ]]; then
  log "ExitAfterReady is set; stopping after successful smoke check"
  exit 0
fi

while true; do
  if ! kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    fail "Backend process stopped"
  fi
  if ! kill -0 "$SERVICE_DESK_PID" >/dev/null 2>&1; then
    fail "Service Desk backend process stopped"
  fi
  if ! kill -0 "$FRONTEND_PID" >/dev/null 2>&1; then
    fail "Frontend process stopped"
  fi
  sleep 2
done
