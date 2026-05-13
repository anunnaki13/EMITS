#!/usr/bin/env bash
set -euo pipefail

# One-command operator status check for the single-host EMITS deployment.

APP_DIR="${EMITS_APP_DIR:-/opt/pltu-tenayan/app}"
BASE_URL="${EMITS_BASE_URL:-http://127.0.0.1:8013}"
FRONTEND_URL="${EMITS_FRONTEND_URL:-http://127.0.0.1}"
BACKEND_SERVICE="${EMITS_BACKEND_SERVICE:-emits-backend}"
DEPLOY_BACKUP_DIR="${EMITS_BACKUP_DIR:-/opt/pltu-tenayan/backups/deploy}"
PYTHON_BIN="${EMITS_PYTHON_BIN:-$APP_DIR/backend/.venv/bin/python}"

status=0

pass() {
  printf 'PASS %-24s %s\n' "$1" "$2"
}

fail() {
  printf 'FAIL %-24s %s\n' "$1" "$2"
  status=1
}

skip() {
  printf 'SKIP %-24s %s\n' "$1" "$2"
}

latest_path() {
  local dir="$1"
  if [ ! -d "$dir" ]; then
    return 1
  fi
  find "$dir" -mindepth 1 -maxdepth 1 -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2-
}

cd "$APP_DIR"

if [ -f "$APP_DIR/backend/.env" ]; then
  set -a
  . "$APP_DIR/backend/.env"
  set +a
fi

SMOKE_EVIDENCE_DIR="${SMOKE_EVIDENCE_DIR:-/var/log/emits/smoke}"
MANAGED_BACKUP_DIR="${EMITS_MANAGED_BACKUP_DIR:-${BACKUP_DIR:-$APP_DIR/backend/backups}}"

if curl -fsS "$BASE_URL/api/health" >/dev/null; then
  pass "backend health" "$BASE_URL/api/health"
else
  fail "backend health" "$BASE_URL/api/health unreachable"
fi

if curl -fsS "$FRONTEND_URL" >/dev/null; then
  pass "frontend static" "$FRONTEND_URL"
else
  fail "frontend static" "$FRONTEND_URL unreachable"
fi

if command -v systemctl >/dev/null 2>&1; then
  if systemctl is-active --quiet "$BACKEND_SERVICE"; then
    pass "systemd service" "$BACKEND_SERVICE active"
  else
    fail "systemd service" "$BACKEND_SERVICE not active"
  fi
else
  skip "systemd service" "systemctl not available"
fi

if command -v nginx >/dev/null 2>&1; then
  if nginx -t >/tmp/emits-nginx-check.log 2>&1; then
    pass "nginx -t" "configuration valid"
  else
    fail "nginx -t" "configuration invalid; see /tmp/emits-nginx-check.log"
  fi
else
  skip "nginx -t" "nginx not available"
fi

if command -v df >/dev/null 2>&1; then
  df -h "${FRONTEND_STATIC_ROOT:-/var/www/emits}" 2>/dev/null || df -h /
else
  skip "disk usage" "df not available"
fi

if latest="$(latest_path "$DEPLOY_BACKUP_DIR")" && [ -n "$latest" ]; then
  pass "deploy backup" "$latest"
else
  skip "deploy backup" "$DEPLOY_BACKUP_DIR empty or missing"
fi

if latest="$(latest_path "$MANAGED_BACKUP_DIR")" && [ -n "$latest" ]; then
  pass "managed backup" "$latest"
else
  skip "managed backup" "$MANAGED_BACKUP_DIR empty or missing"
fi

mkdir -p "$SMOKE_EVIDENCE_DIR" 2>/dev/null || {
  sudo mkdir -p "$SMOKE_EVIDENCE_DIR"
  sudo chown "$(id -u):$(id -g)" "$SMOKE_EVIDENCE_DIR" || true
}

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
smoke_evidence="$SMOKE_EVIDENCE_DIR/status-smoke-$timestamp.json"
smoke_args=(
  --base-url "$BASE_URL"
  --frontend-url "$FRONTEND_URL"
  --json-output "$smoke_evidence"
)
if [ -n "${TEST_ADMIN_EMAIL:-}" ] && [ -n "${TEST_ADMIN_PASSWORD:-}" ]; then
  smoke_args+=(--record-status)
fi

if "$PYTHON_BIN" "$APP_DIR/ops/scripts/smoke_check.py" "${smoke_args[@]}"; then
  pass "smoke check" "$smoke_evidence"
else
  fail "smoke check" "$smoke_evidence"
fi

exit "$status"
