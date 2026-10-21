#!/bin/sh
set -eu
: "${PLATFORM_ACCESS_UPSTREAM:?Set PLATFORM_ACCESS_UPSTREAM}"
: "${PLATFORM_PROJECTS_UPSTREAM:?Set PLATFORM_PROJECTS_UPSTREAM}"
case "$PLATFORM_ACCESS_UPSTREAM" in https://*) ;; *) echo 'Access upstream must be HTTPS' >&2; exit 1;; esac
case "$PLATFORM_PROJECTS_UPSTREAM" in https://*) ;; *) echo 'Projects upstream must be HTTPS' >&2; exit 1;; esac
PORT="${PORT:-8080}"
NGINX_RESOLVER="$(awk '/^nameserver[[:space:]]/{print $2; exit}' /etc/resolv.conf)"
: "${NGINX_RESOLVER:?No DNS resolver found in /etc/resolv.conf}"
export PORT PLATFORM_ACCESS_UPSTREAM PLATFORM_PROJECTS_UPSTREAM NGINX_RESOLVER
envsubst '${PORT} ${PLATFORM_ACCESS_UPSTREAM} ${PLATFORM_PROJECTS_UPSTREAM} ${NGINX_RESOLVER}' \
    < /etc/nginx/relaxdev.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g 'daemon off;'
