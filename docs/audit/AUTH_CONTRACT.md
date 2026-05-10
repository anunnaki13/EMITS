# Auth Contract Reconciliation

**Phase:** 02-authentication-stabilization
**Plan:** 02-02
**Closed:** 2026-05-10
**Locks:** AUTHFIX-01 (session persistence) + AUTHFIX-02 (HTTP error codes)
**Spec source:** `.planning/intel/constraints.md` → CONS-auth-header

## Status

AUTHFIX-01 and AUTHFIX-02 closed by Plan 02-02. **5/5 regression tests pass** against a locally-spun-up uvicorn instance pointed at an isolated test database (`pltu_tenayan_test_02_02`) — production data on the remote VPS was NOT touched. The two contract divergences flagged in Phase 1 (LOGIN_BUG.md "Path B Divergence") are resolved here:

1. **422 → 400** for malformed `/api/auth/*` bodies — fixed by a custom `RequestValidationError` handler.
2. **401 vs. 403** for missing-Authorization-header — accepted as-is and documented (FastAPI `HTTPBearer` security default; the 401 path for invalid/expired token still works correctly).

## Decisions

| Decision | Source divergence | Resolution | Rationale |
|----------|-------------------|------------|-----------|
| **D-AUTH-01** | `/api/auth/*` malformed body returned 422 (FastAPI Pydantic default) | Custom `auth_validation_handler` in `backend/server.py` re-emits HTTP 400 for paths that startwith `/api/auth/` only | CONS-auth-header is locked SPEC; downstream API_REFERENCE.md / DOCS-01 expects 400. Scoping by path prefix prevents cross-route blast radius — vessels/COA/etc. keep FastAPI's standard 422. Frontend `Login.js:37` toast handler reads `error.response?.data?.detail` which works for both 400 and 422 (no FE break). Single-line conditional, pinpointed by `test_login_with_malformed_body_returns_400`. |
| **D-AUTH-02** | Missing-Authorization-header returns 403, not 401 | Accept as-is; document explicitly | FastAPI `HTTPBearer()` raises `HTTPException(403)` when no `Authorization` header is present. CONS-auth-header's 401 is semantically for "invalid/expired token" — that path **still returns 401** (verified by `test_me_with_expired_token_returns_401`, which forges a JWT with `exp` 5 minutes in the past). Changing the 403→401 for the missing-header path requires overriding the security dependency, which has cross-route blast radius (every protected endpoint). The accept-as-is disposition is the documented contract going forward. |

## Verified contract (post-fix)

The six confirmed status codes for the `/api/auth/*` surface, each pinned by a test in `backend/tests/test_auth_session.py`:

| Status | Method + Path | Condition | Test name |
|--------|---------------|-----------|-----------|
| **200** | POST /api/auth/login | valid creds | `test_login_then_me_rehydrates_same_user` |
| **200** | GET  /api/auth/me | valid token | `test_login_then_me_rehydrates_same_user` |
| **400** | POST /api/auth/login | malformed body | `test_login_with_malformed_body_returns_400` |
| **401** | POST /api/auth/login | bad password | `test_login_with_invalid_password_returns_401` |
| **401** | GET  /api/auth/me | expired token | `test_me_with_expired_token_returns_401` |
| **403** | GET  /api/auth/me | no Authorization header | `test_me_without_token_returns_403` |

`test_login_then_me_rehydrates_same_user` proves AUTHFIX-01: the token issued by `/api/auth/login` round-trips the **same user identity** through `/api/auth/me` — exactly the rehydrate path `AuthContext.js:13-32` exercises on every page load. Session persistence is verified end-to-end.

## Code change

**File:** `backend/server.py` (head of file, after the `app = FastAPI(...)` line — before the first router include).

```python
# AUTHFIX-02: CONS-auth-header locks 400 for validation failures on /api/auth/*.
# FastAPI's default is 422; remap only for the auth scope so other routes keep
# FastAPI's standard 422 default (no contract divergence elsewhere).
@app.exception_handler(RequestValidationError)
async def auth_validation_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api/auth/"):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.errors()},
        )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
```

**Rationale for path-prefix scoping (not router-level registration):** The handler is registered on the `FastAPI` app instance. FastAPI does not support registering a `RequestValidationError` handler on an `APIRouter` — only on the `app`. Path-prefix scoping `request.url.path.startswith("/api/auth/")` is the cleanest way to limit the 400 remap to the auth surface; non-auth routes (vessels, COA, smart-stock, AI) flow through the unscoped 422 fallback inside the same handler. When Phase 7 (UPGRADE-01) eventually mounts `backend/routers/auth.py` instead of the inline handlers in `server.py`, this handler **continues to apply automatically** (it scopes by URL path, not by router) — the parity comment at the top of `routers/auth.py` records this for future readers.

## Frontend impact

`AuthContext.js:13-32` already implements the rehydrate path correctly (Phase 1 audit confirmed). **No frontend code changed in this plan.** The `Login.js:37` toast handler reads `error.response?.data?.detail`, which works identically for both 400 and 422 responses — the 422→400 change is invisible to the user-facing flow. The pre-existing ResizeObserver suppressor at `frontend/public/index.html:49–65` is untouched (Phase-1 LOGIN_BUG.md noted it as register-tab-only noise, not a login bug; outside this plan's scope).

## Test runbook

The regression suite lives at `backend/tests/test_auth_session.py` and consumes fixtures from `backend/tests/conftest.py`. **All credentials must be sourced from environment variables** — DO NOT inline credentials in committed files (the `scripts/check_credentials.sh` pre-commit hook will block any such commit per AUTHFIX-05).

### Local-process invocation (recommended for dev/CI)

For local execution against an isolated FastAPI instance pointed at a throwaway test DB (the approach this plan used). All passwords are sourced from the gitignored `memory/test_credentials.md` — never inlined.

```bash
# 1. Source secrets into the shell from memory/test_credentials.md (gitignored).
#    Append OPERATOR/VIEWER sections to that file before first run if missing.
cd pltu-tenayan-full-backup
export TEST_ADMIN_EMAIL="$(awk '/^## Akun Admin$/,/^##/{ if(/Email:/){sub(/^- Email:[[:space:]]*/,"");print;exit} }' memory/test_credentials.md)"
export TEST_ADMIN_PASSWORD="$(awk '/^## Akun Admin$/,/^##/{ if(/Password:/){sub(/^- Password:[[:space:]]*/,"");print;exit} }' memory/test_credentials.md)"
# Repeat the two-line pattern above for "## Akun Operator" / "## Akun Viewer" → TEST_OPERATOR_*/TEST_VIEWER_*
export JWT_SECRET="$(grep -E '^JWT_SECRET=' backend/.env | cut -d= -f2-)"

# 2. Spin up a local backend on port 8013 against a throwaway test database
TEST_DB=pltu_tenayan_test_02_02
mongosh --quiet --eval "db.getSiblingDB('${TEST_DB}').dropDatabase()" || true
( cd backend && \
  MONGO_URL=mongodb://localhost:27017 DB_NAME=${TEST_DB} \
  JWT_SECRET="${JWT_SECRET}" CORS_ORIGINS=http://localhost:3013 \
  nohup .venv/bin/uvicorn server:app --host 127.0.0.1 --port 8013 \
    > /tmp/emits-test-server.log 2>&1 & )
sleep 3

# 3. Seed admin/operator/viewer in the test DB via /api/auth/register
for role in admin operator viewer; do
  case "$role" in
    admin)    EMAIL="$TEST_ADMIN_EMAIL";    PW="$TEST_ADMIN_PASSWORD";    NAME="Admin"    ;;
    operator) EMAIL="$TEST_OPERATOR_EMAIL"; PW="$TEST_OPERATOR_PASSWORD"; NAME="Operator" ;;
    viewer)   EMAIL="$TEST_VIEWER_EMAIL";   PW="$TEST_VIEWER_PASSWORD";   NAME="Viewer"   ;;
  esac
  curl -s -X POST http://localhost:8013/api/auth/register \
    -H "Content-Type: application/json" \
    -d "$(python3 -c "import json,sys;print(json.dumps({'email':'$EMAIL','password':'$PW','name':'$NAME','role':'$role'}))")" >/dev/null
done

# 4. Run the regression suite — env-var sourced, no inline literals
REACT_APP_BACKEND_URL=http://localhost:8013 \
JWT_ALGORITHM=HS256 \
MONGO_URL=mongodb://localhost:27017 DB_NAME=${TEST_DB} \
  backend/.venv/bin/pytest backend/tests/test_auth_session.py -v --tb=short
# Expected: 5 passed in <2s

# 5. Tear down
pkill -f 'uvicorn server:app --host 127.0.0.1 --port 8013'
mongosh --quiet --eval "db.getSiblingDB('${TEST_DB}').dropDatabase()" || true
unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD TEST_OPERATOR_EMAIL TEST_OPERATOR_PASSWORD TEST_VIEWER_EMAIL TEST_VIEWER_PASSWORD JWT_SECRET
```

### VPS-targeted invocation (Phase-1 idiom — read-only against live)

For ad-hoc verification against the production VPS. Login + /me are read-only against the live `users` collection; the suite makes NO writes (no register calls). Skipped fixtures (`operator/viewer`) are tolerated.

```bash
cd pltu-tenayan-full-backup
export REACT_APP_BACKEND_URL=http://103.150.197.225:8013
# Source from gitignored memory/test_credentials.md
export TEST_ADMIN_EMAIL="$(awk '/^## Akun Admin$/,/^##/{ if(/Email:/){sub(/^- Email:[[:space:]]*/,"");print;exit} }' memory/test_credentials.md)"
export TEST_ADMIN_PASSWORD="$(awk '/^## Akun Admin$/,/^##/{ if(/Password:/){sub(/^- Password:[[:space:]]*/,"");print;exit} }' memory/test_credentials.md)"
export JWT_SECRET="$(grep -E '^JWT_SECRET=' backend/.env | cut -d= -f2-)"
backend/.venv/bin/pytest backend/tests/test_auth_session.py -v --tb=short
unset TEST_ADMIN_EMAIL TEST_ADMIN_PASSWORD JWT_SECRET
```

> **Reminder:** DO NOT inline credentials in committed files. The pre-commit hook from Plan 02-01 (`scripts/check_credentials.sh`) will reject commits that embed admin/operator/viewer passwords or JWT-shaped strings. See `docs/audit/CREDENTIAL_HYGIENE.md` for the env-var contract.

## Phase-3 follow-ups

- **DOCS-01 / API_REFERENCE.md:** Update the `/api/auth/login` and `/api/auth/register` sections to document **400** (not 422) for malformed-body validation failures. Cite this document and the locking test `test_login_with_malformed_body_returns_400`.
- **DOCS-01 / API_REFERENCE.md:** Document the explicit **403-vs-401 split** for `/api/auth/me`: 403 when no `Authorization` header is sent (FastAPI HTTPBearer default), 401 when a token is present but invalid/expired. Cite D-AUTH-02 here.
- **OPS-AUDIT (Phase 5):** The 3 `audit-probe-*@audit-probes-2026.com` synthetic users from Phase-1 plan 01-04 still live in the production `users` collection. The conftest cleanup operates on whatever DB `DB_NAME` points to (defaulting to `pltu_tenayan`); if test runners ever execute against the production DB (NOT recommended), they would be removed automatically. Cleanup filter for manual ops: `db.users.deleteMany({email: /^audit-probe-/})`.
