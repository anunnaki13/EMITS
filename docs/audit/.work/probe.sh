#!/usr/bin/env bash
# Probe live /api/* endpoints and emit a CSV-like inventory plus pagination spot-check.
# Token is sourced from memory/test_credentials.md at probe time and never written to disk.
set -u

HOST="http://103.150.197.225:8013"
WORKDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$WORKDIR/../../.." && pwd)"
CREDS_FILE="$ROOT/memory/test_credentials.md"

# Build login payload from creds without writing to a tracked file.
EMAIL=$(grep -oE 'Email:[[:space:]]*[^[:space:]]+' "$CREDS_FILE" | awk '{print $2}')
PASS=$(grep -oE 'Password:[[:space:]]*[^[:space:]]+' "$CREDS_FILE" | awk '{print $2}')

TMP_LOGIN=$(mktemp)
trap "rm -f $TMP_LOGIN" EXIT
printf '{"email":"%s","password":"%s"}' "$EMAIL" "$PASS" > "$TMP_LOGIN"
TOKEN=$(curl -sS -X POST "$HOST/api/auth/login" -H 'Content-Type: application/json' -d "@$TMP_LOGIN" | jq -r '.access_token // .token // empty')
rm -f "$TMP_LOGIN"

if [ -z "$TOKEN" ]; then
  echo "LOGIN_FAILED" >&2
  TOKEN=""
fi

OPENAPI="$WORKDIR/openapi.json"

# Output inventory CSV: path|methods|auth|http_codes_per_method|status
INV="$WORKDIR/inventory.csv"
PAGN="$WORKDIR/pagination.csv"
PUBLIC="$WORKDIR/public-probes.csv"
> "$INV"
> "$PAGN"
> "$PUBLIC"

# Public endpoints to probe without auth
probe_public() {
  for url in "/api/" "/api/health"; do
    code=$(curl -sS -o /dev/null -w '%{http_code}' "$HOST$url")
    echo "$url|GET|$code" >> "$PUBLIC"
  done
  # POST login & register with empty body to see how they behave (no actual mutation)
  code=$(curl -sS -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "$HOST/api/auth/login")
  echo "/api/auth/login|POST(empty-body)|$code" >> "$PUBLIC"
  code=$(curl -sS -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "$HOST/api/auth/register")
  echo "/api/auth/register|POST(empty-body)|$code" >> "$PUBLIC"
}

# For each path in openapi: list methods, security, and probe GET-with-no-path-params live
PATHS=$(jq -r '.paths | keys[]' "$OPENAPI")
while IFS= read -r path; do
  methods=$(jq -r --arg p "$path" '.paths[$p] | keys | map(ascii_upcase) | join(",")' "$OPENAPI")
  # Determine auth: any operation with non-empty `security` => required; otherwise look at the openapi global security
  has_security=$(jq -r --arg p "$path" '
    .paths[$p]
    | to_entries
    | map(select(.value.security != null and (.value.security | length > 0)))
    | length' "$OPENAPI")
  global_sec=$(jq -r '(.security // []) | length' "$OPENAPI")
  # FastAPI generated docs: per-route security is set when Depends(get_current_user) is used.
  # For routes without explicit security entries, infer from the path: only the documented public set is public.
  case "$path" in
    /api/|/api/health|/api/auth/login|/api/auth/register)
      auth="public"
      ;;
    *)
      if [ "$has_security" -gt 0 ] || [ "$global_sec" -gt 0 ]; then
        auth="required"
      else
        # Inferred: not in public set => assume required (CONS-auth-header).
        auth="required-inferred"
      fi
      ;;
  esac

  # Collect per-method codes for GETs without path params
  codes=""
  status="not-probed-mutating"
  if [[ "$methods" == *"GET"* ]]; then
    if [[ "$path" == *"{"* ]]; then
      status="not-probed-path-param"
      codes="GET=skipped(path-param)"
    else
      # Probe GET
      if [[ "$auth" == "public" ]]; then
        code=$(curl -sS -o /dev/null -w '%{http_code}' "$HOST$path")
      else
        if [ -n "$TOKEN" ]; then
          code=$(curl -sS -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" "$HOST$path")
        else
          code="auth-unverified"
        fi
      fi
      codes="GET=$code"
      # Status mapping
      case "$code" in
        200|201|204) status="working" ;;
        401)
          if [[ "$auth" == "required" || "$auth" == "required-inferred" ]]; then status="working-auth-required"
          else status="broken-auth-leak"; fi
          ;;
        403) status="working-role-gated" ;;
        404) status="broken-not-found" ;;
        5*)  status="broken-5xx" ;;
        000) status="broken-unreachable" ;;
        auth-unverified) status="unverified-auth" ;;
        *)   status="other-$code" ;;
      esac
    fi
  fi

  # GET path-param + only-mutating endpoint marker (status already set)
  echo "$path|$methods|$auth|$codes|$status" >> "$INV"
done <<< "$PATHS"

probe_public

# Pagination spot-check: probe ?page=1&page_size=1 against list endpoints
list_eps=(
  /api/vessels
  /api/barges
  /api/trucking
  /api/biomassa
  /api/po-batubara
  /api/merit-order
  /api/coa-reconciliation
  /api/smart-stock
  /api/sumber-pemakaian
  /api/ai/sessions
)
for ep in "${list_eps[@]}"; do
  if [ -n "$TOKEN" ]; then
    body=$(curl -sS -H "Authorization: Bearer $TOKEN" "$HOST$ep?page=1&page_size=1")
  else
    body=$(curl -sS "$HOST$ep?page=1&page_size=1")
  fi
  keys=$(echo "$body" | jq -r 'if type == "object" then (keys | sort | join(",")) else "non-object" end' 2>/dev/null || echo "parse-error")
  echo "$ep|$keys" >> "$PAGN"
done

# Public probe summary
echo "--- INVENTORY ---"
cat "$INV"
echo "--- PAGINATION ---"
cat "$PAGN"
echo "--- PUBLIC ---"
cat "$PUBLIC"
