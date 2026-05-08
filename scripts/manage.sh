#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-$(pwd)}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ACTION="${1:-status}"
shift || true

log() {
  printf '[manage] %s\n' "$*"
}

die() {
  printf '[manage] error: %s\n' "$*" >&2
  exit 1
}

choose_compose() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
    return
  fi
  die "docker compose is not installed"
}

require_repo_files() {
  [ -f "${APP_DIR}/${COMPOSE_FILE}" ] || die "missing ${COMPOSE_FILE} in ${APP_DIR}"
  [ -f "${APP_DIR}/.env" ] || die "missing .env in ${APP_DIR}"
}

compose() {
  (
    cd "$APP_DIR"
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" "$@"
  )
}

choose_compose
require_repo_files

case "$ACTION" in
  up|start)
    log "starting services"
    compose up -d --build "$@"
    ;;
  down|stop)
    log "stopping services"
    compose down "$@"
    ;;
  restart)
    log "restarting services"
    compose restart "$@"
    ;;
  status|ps)
    compose ps "$@"
    ;;
  logs)
    compose logs -f --tail=200 "$@"
    ;;
  update)
    log "pulling repository updates"
    git -C "$APP_DIR" fetch origin
    git -C "$APP_DIR" pull --ff-only
    compose up -d --build "$@"
    ;;
  build)
    log "building images"
    compose build "$@"
    ;;
  shell)
    compose exec manager bash "$@"
    ;;
  *)
    cat <<'EOF'
Usage: scripts/manage.sh <action>

Actions:
  up|start      Build and start services
  down|stop     Stop services
  restart       Restart services
  status|ps     Show service status
  logs          Follow service logs
  update        Pull latest code and recreate services
  build         Build images only
  shell         Open a shell in the manager container
EOF
    exit 1
    ;;
esac
