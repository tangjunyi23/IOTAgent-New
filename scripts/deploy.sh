#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="${REPO_URL:-https://github.com/tangjunyi23/IOTAgent-New.git}"
BRANCH="${BRANCH:-main}"
APP_DIR="${APP_DIR:-/srv/iot-agent-new}"
APP_PORT="${APP_PORT:-10000}"
ENABLE_DOCKER_RUNTIME="${ENABLE_DOCKER_RUNTIME:-true}"
SUBAGENT_DOCKER_IMAGE="${SUBAGENT_DOCKER_IMAGE:-binary-audit-subagent:latest}"
SUBAGENT_DOCKER_NETWORK_MODE="${SUBAGENT_DOCKER_NETWORK_MODE:-auto}"
MANAGER_REGULAR_MODEL="${MANAGER_REGULAR_MODEL:-deepseek-v4-flash}"
MANAGER_HARD_MODEL="${MANAGER_HARD_MODEL:-deepseek-v4-pro}"
DEEPSEEK_BASE_URL="${DEEPSEEK_BASE_URL:-https://api.deepseek.com}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-iot-agent-new}"

log() {
  printf '[deploy] %s\n' "$*"
}

warn() {
  printf '[deploy] warning: %s\n' "$*" >&2
}

die() {
  printf '[deploy] error: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
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

read_env_value() {
  local key="$1"
  local file="$2"
  if [ ! -f "$file" ]; then
    return 0
  fi
  grep -E "^${key}=" "$file" | tail -n 1 | cut -d'=' -f2- || true
}

upsert_env() {
  local key="$1"
  local value="$2"
  local file="$3"
  local escaped
  escaped="$(printf '%s' "$value" | sed 's/[&|]/\\&/g')"
  if grep -q -E "^${key}=" "$file"; then
    sed -i "s|^${key}=.*$|${key}=${escaped}|" "$file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$file"
  fi
}

set_env_default() {
  local key="$1"
  local preferred="$2"
  local fallback="$3"
  local file="$4"
  local current
  current="$(read_env_value "$key" "$file")"
  if [ -n "$preferred" ]; then
    upsert_env "$key" "$preferred" "$file"
    return
  fi
  if [ -n "$current" ]; then
    return
  fi
  upsert_env "$key" "$fallback" "$file"
}

wait_for_health() {
  local port="$1"
  if ! command -v curl >/dev/null 2>&1; then
    warn "curl is not installed on host, skipping HTTP health probe"
    return 0
  fi
  local attempt
  for attempt in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:${port}/api/v1/health" >/dev/null 2>&1; then
      log "service is healthy on port ${port}"
      return 0
    fi
    sleep 2
  done
  warn "service did not pass health probe within timeout"
  return 1
}

require_command git
require_command docker
choose_compose

mkdir -p "$(dirname "$APP_DIR")"
if [ ! -d "$APP_DIR/.git" ]; then
  log "cloning ${REPO_URL} into ${APP_DIR}"
  git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
else
  log "updating repository in ${APP_DIR}"
  git -C "$APP_DIR" fetch origin "$BRANCH"
  git -C "$APP_DIR" checkout "$BRANCH"
  git -C "$APP_DIR" pull --ff-only origin "$BRANCH"
fi

cd "$APP_DIR"

[ -f ".env.example" ] || die ".env.example not found in ${APP_DIR}"
[ -f "docker-compose.prod.yml" ] || die "docker-compose.prod.yml not found in ${APP_DIR}"

if [ ! -f ".env" ]; then
  log "creating .env from .env.example"
  cp .env.example .env
fi

set_env_default DEEPSEEK_BASE_URL "${DEEPSEEK_BASE_URL:-}" "https://api.deepseek.com" ".env"
set_env_default MANAGER_REGULAR_MODEL "${MANAGER_REGULAR_MODEL:-}" "deepseek-v4-flash" ".env"
set_env_default MANAGER_HARD_MODEL "${MANAGER_HARD_MODEL:-}" "deepseek-v4-pro" ".env"
set_env_default ENABLE_DOCKER_RUNTIME "${ENABLE_DOCKER_RUNTIME:-}" "true" ".env"
set_env_default SUBAGENT_DOCKER_IMAGE "${SUBAGENT_DOCKER_IMAGE:-}" "binary-audit-subagent:latest" ".env"
set_env_default SUBAGENT_DOCKER_NETWORK_MODE "${SUBAGENT_DOCKER_NETWORK_MODE:-}" "auto" ".env"
set_env_default COMPOSE_PROJECT_NAME "${COMPOSE_PROJECT_NAME:-}" "iot-agent-new" ".env"
set_env_default APP_PORT "${APP_PORT:-}" "10000" ".env"
upsert_env HOST_WORKSPACE_DIR "$APP_DIR" ".env"

if [ -n "${DEEPSEEK_API_KEY:-}" ]; then
  upsert_env DEEPSEEK_API_KEY "$DEEPSEEK_API_KEY" ".env"
fi
if [ -z "$(read_env_value DEEPSEEK_API_KEY ".env")" ]; then
  die "DEEPSEEK_API_KEY is empty. Export it before running, for example: DEEPSEEK_API_KEY=xxx bash scripts/deploy.sh"
fi

mkdir -p data/uploads data/audits data/artifacts data/runtime data/knowledge

if [ "$(read_env_value ENABLE_DOCKER_RUNTIME ".env")" = "true" ]; then
  [ -S /var/run/docker.sock ] || die "/var/run/docker.sock is required when ENABLE_DOCKER_RUNTIME=true"
  log "building sub-agent image ${SUBAGENT_DOCKER_IMAGE}"
  docker build -f Dockerfile.subagent -t "${SUBAGENT_DOCKER_IMAGE}" .
else
  warn "ENABLE_DOCKER_RUNTIME=false, manager will run sub-agents in-process"
fi

log "starting platform with docker compose"
"${COMPOSE_CMD[@]}" -f docker-compose.prod.yml up -d --build
"${COMPOSE_CMD[@]}" -f docker-compose.prod.yml ps

resolved_port="$(read_env_value APP_PORT ".env")"
wait_for_health "${resolved_port}" || true

host_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -z "${host_ip}" ]; then
  host_ip="127.0.0.1"
fi

log "deployment finished"
log "frontend: http://${host_ip}:${resolved_port}/"
