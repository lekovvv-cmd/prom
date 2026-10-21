#!/bin/sh
set -eu

# Runs only when postgres_data is first initialized. Each module owns its own database.
modules="prom_access project_showcase"
if [ "${ENABLE_SERVICE_DESK_DATABASE:-true}" = "true" ]; then
  modules="$modules service_desk"
fi

for module in $modules; do
  case "$module" in
    prom_access) password=$ACCESS_DB_PASSWORD ;;
    project_showcase) password=$PROJECTS_DB_PASSWORD ;;
    service_desk) password=$SERVICE_DESK_DB_PASSWORD ;;
  esac
  escaped_password=$(printf '%s' "$password" | sed "s/'/''/g")
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
    -c "CREATE ROLE \"$module\" LOGIN PASSWORD '$escaped_password'"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
    -c "CREATE DATABASE \"$module\" OWNER \"$module\""
done
