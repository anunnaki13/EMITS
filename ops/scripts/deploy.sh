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
"$APP_DIR/backend/.venv/bin/python" "$APP_DIR/ops/scripts/smoke_check.py" \
  --base-url "$BASE_URL" \
  --frontend-url "$FRONTEND_URL"

echo "Deploy complete. Backup snapshot: $BACKUP_DIR/$timestamp"
