#!/usr/bin/env bash
set -Eeuo pipefail

REPO_URL="${REPO_URL:-https://github.com/tangjunyi23/IOTAgent-New.git}"
BRANCH="${BRANCH:-main}"

log() {
  printf '[bootstrap] %s\n' "$*"
}

die() {
  printf '[bootstrap] error: %s\n' "$*" >&2
  exit 1
}

fetch_remote_script() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url"
    return
  fi
  if command -v wget >/dev/null 2>&1; then
    wget -qO- "$url"
    return
  fi
  die "curl or wget is required to download deploy.sh"
}

build_script_url() {
  case "$REPO_URL" in
    https://github.com/*)
      local repo_path="${REPO_URL#https://github.com/}"
      repo_path="${repo_path%.git}"
      printf 'https://raw.githubusercontent.com/%s/%s/scripts/deploy.sh\n' "$repo_path" "$BRANCH"
      ;;
    *)
      die "bootstrap-linux.sh currently supports GitHub repositories only"
      ;;
  esac
}

SCRIPT_URL="$(build_script_url)"
log "delegating to ${SCRIPT_URL}"
fetch_remote_script "$SCRIPT_URL" | bash
