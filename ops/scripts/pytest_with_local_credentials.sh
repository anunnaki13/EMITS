#!/usr/bin/env bash
set -euo pipefail

# Runs focused pytest commands after loading test credentials from the local,
# gitignored memory/test_credentials.md. The secrets are never printed.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CREDENTIAL_FILE="${EMITS_TEST_CREDENTIAL_FILE:-$ROOT_DIR/memory/test_credentials.md}"

if [ ! -f "$CREDENTIAL_FILE" ]; then
  echo "Missing $CREDENTIAL_FILE" >&2
  echo "Create it from the secure operational source; never commit it." >&2
  exit 1
fi

extract_field() {
  local section="$1"
  local label="$2"
  awk -v section="$section" -v label="$label" '
    $0 == "## " section { in_section=1; next }
    in_section && /^## / { exit }
    in_section && index($0, "- " label ":") == 1 {
      sub("^- " label ":[[:space:]]*", "")
      print
      exit
    }
  ' "$CREDENTIAL_FILE"
}

export TEST_ADMIN_EMAIL="$(extract_field "Akun Admin" "Email")"
export TEST_ADMIN_PASSWORD="$(extract_field "Akun Admin" "Password")"
export TEST_OPERATOR_EMAIL="$(extract_field "Akun Operator" "Email")"
export TEST_OPERATOR_PASSWORD="$(extract_field "Akun Operator" "Password")"
export TEST_VIEWER_EMAIL="$(extract_field "Akun Viewer" "Email")"
export TEST_VIEWER_PASSWORD="$(extract_field "Akun Viewer" "Password")"
export MONGO_URL="${MONGO_URL:-mongodb://localhost:27017}"
export DB_NAME="${DB_NAME:-pltu_tenayan}"

if [ -f "$ROOT_DIR/backend/.env" ] && [ -z "${JWT_SECRET:-}" ]; then
  JWT_SECRET="$(awk -F= '/^JWT_SECRET=/{sub(/^JWT_SECRET=/,""); print; exit}' "$ROOT_DIR/backend/.env")"
  export JWT_SECRET
fi

cd "$ROOT_DIR/backend"
if [ "$#" -eq 0 ]; then
  set -- tests/ -q
fi
exec ./.venv/bin/python -m pytest "$@"
