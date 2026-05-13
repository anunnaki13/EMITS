#!/usr/bin/env bash
set -euo pipefail

# Repeatable deploy helper for a single-host EMITS installation.
# Defaults match the documented production layout; override with env vars if needed.

APP_DIR="${EMITS_APP_DIR:-/opt/pltu-tenayan/app}"
WEB_ROOT="${EMITS_WEB_ROOT:-/var/www/emits}"
BACKEND_SERVICE="${EMITS_BACKEND_SERVICE:-emits-backend}"
BACKUP_DIR="${EMITS_BACKUP_DIR:-/opt/pltu-tenayan/backups/deploy}"
BASE_URL="${EMITS_BASE_URL:-http://127.0.0.1:8013}"
FRONTEND_URL="${EMITS_FRONTEND_URL:-http://127.0.0.1}"

cd "$APP_DIR"

echo "==> Checking working tree"
git diff --quiet
git diff --cached --quiet

echo "==> Updating source"
git pull --ff-only

echo "==> Loading backend env for backup"
set -a
. "$APP_DIR/backend/.env"
set +a
SMOKE_EVIDENCE_DIR="${SMOKE_EVIDENCE_DIR:-/var/log/emits/smoke}"

echo "==> Creating pre-deploy MongoDB backup"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR/$timestamp"
mongodump --uri="$MONGO_URL" --db="$DB_NAME" --out "$BACKUP_DIR/$timestamp"

echo "==> Installing backend dependencies"
if [ ! -x "$APP_DIR/backend/.venv/bin/python" ]; then
  python3 -m venv "$APP_DIR/backend/.venv"
fi
"$APP_DIR/backend/.venv/bin/pip" install --upgrade pip
"$APP_DIR/backend/.venv/bin/pip" install -r "$APP_DIR/backend/requirements.txt"

echo "==> Building frontend"
cd "$APP_DIR/frontend"
yarn install --frozen-lockfile
yarn build

echo "==> Publishing frontend build to $WEB_ROOT"
sudo mkdir -p "$WEB_ROOT"
sudo rsync -a --delete "$APP_DIR/frontend/build/" "$WEB_ROOT/"

echo "==> Restarting backend and reloading nginx"
sudo systemctl restart "$BACKEND_SERVICE"
sudo systemctl reload nginx

echo "==> Running smoke check"
cd "$APP_DIR"
sudo mkdir -p "$SMOKE_EVIDENCE_DIR"
sudo chown "$(id -u):$(id -g)" "$SMOKE_EVIDENCE_DIR" || true
smoke_evidence="$SMOKE_EVIDENCE_DIR/deploy-smoke-$timestamp.json"
smoke_args=(
  --base-url "$BASE_URL"
  --frontend-url "$FRONTEND_URL"
  --json-output "$smoke_evidence"
)
if [ -n "${TEST_ADMIN_EMAIL:-}" ] && [ -n "${TEST_ADMIN_PASSWORD:-}" ]; then
  smoke_args+=(--record-status)
fi
"$APP_DIR/backend/.venv/bin/python" "$APP_DIR/ops/scripts/smoke_check.py" \
  "${smoke_args[@]}"

echo "Deploy complete. Backup snapshot: $BACKUP_DIR/$timestamp"
echo "Smoke evidence: $smoke_evidence"
