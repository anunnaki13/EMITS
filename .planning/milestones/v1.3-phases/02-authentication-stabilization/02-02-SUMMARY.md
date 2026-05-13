---
phase: 02-authentication-stabilization
plan: 02
subsystem: auth-contract
tags: [authfix-01, authfix-02, regression-tests, request-validation-handler, http-contract]
requires:
  - "Plan 02-01 (credential hygiene gate) — provides scripts/check_credentials.sh + env-var contract"
provides:
  - "/api/auth/* malformed-body returns HTTP 400 (not 422), matching CONS-auth-header"
  - "5-test pytest regression suite at backend/tests/test_auth_session.py exercising AUTHFIX-01 + AUTHFIX-02"
  - "backend/tests/conftest.py with 7 named fixtures (env-var-sourced, audit-probe cleanup)"
  - "AUTH_CONTRACT.md decision record locking D-AUTH-01 (422→400) and D-AUTH-02 (401-vs-403)"
affects:
  - "pltu-tenayan-full-backup/backend/server.py"
  - "pltu-tenayan-full-backup/backend/routers/auth.py"
  - "pltu-tenayan-full-backup/backend/tests/conftest.py"
  - "pltu-tenayan-full-backup/backend/tests/test_auth_session.py"
  - "pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md"
tech-stack:
  added: []
  patterns:
    - "Path-prefix-scoped RequestValidationError handler on the FastAPI app instance"
    - "TestClient-vs-live-server hybrid: pytest+requests against locally-spun-up uvicorn pointed at a throwaway test DB"
    - "pytest fixture skip-not-fail when env vars unset (CI-friendly)"
    - "Anchor-prefixed Mongo cleanup filter ({email: {$regex: '^audit-probe-'}}) — cannot match real users"
key-files:
  created:
    - "pltu-tenayan-full-backup/backend/tests/conftest.py (93 lines)"
    - "pltu-tenayan-full-backup/backend/tests/test_auth_session.py (140 lines)"
    - "pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md (138 lines)"
  modified:
    - "pltu-tenayan-full-backup/backend/server.py (+25 lines: imports + auth_validation_handler)"
    - "pltu-tenayan-full-backup/backend/routers/auth.py (+4 lines: AUTHFIX-02 parity comment)"
decisions:
  - "D-AUTH-01: Resolve 422→400 by adding a custom RequestValidationError handler scoped to paths starting with /api/auth/; non-auth routes preserve FastAPI's 422 default."
  - "D-AUTH-02: Accept the 403-on-missing-Authorization-header behavior as the contract; FastAPI HTTPBearer default. The 401-on-invalid/expired-token path still works correctly (verified)."
  - "Test infrastructure: pytest+requests against a locally-spun-up uvicorn pointed at an isolated test DB (pltu_tenayan_test_02_02) — NOT the production VPS, NOT the live pltu_tenayan database. Aligns with system-reminder: 'never the production MongoDB'."
metrics:
  duration: ~7.5min
  completed: 2026-05-10
  tasks_completed: 4
  files_created: 3
  files_modified: 2
  commits_inner: 4
  commits_outer: 1
---

# Phase 02 Plan 02: Auth Session Persistence + Error-Code Contract — Summary

Closes AUTHFIX-01 (session persistence verified by /api/auth/me rehydrate) and AUTHFIX-02 (HTTP error codes aligned with CONS-auth-header). The two contract divergences flagged in Phase-1 LOGIN_BUG.md Path B are resolved: a custom `RequestValidationError` handler remaps 422→400 for paths starting with `/api/auth/` (D-AUTH-01), and the 403-on-missing-Authorization-header behavior is documented and accepted as the contract (D-AUTH-02). The 5-test pytest regression suite at `backend/tests/test_auth_session.py` pins the contract end-to-end and ran 5/5 PASSED (0.99s) against a locally-spun-up uvicorn instance pointed at an isolated test database — production VPS and the live `pltu_tenayan` collection were untouched.

## Inner-repo commits (pltu-tenayan-full-backup/)

| Hash | Subject | Task |
|------|---------|------|
| `34d4c3e` | feat(02-02): add 422→400 RequestValidationError handler scoped to /api/auth/* | Task 1 |
| `54ea64b` | test(02-02): add conftest with env-var-sourced credentials and audit-probe cleanup | Task 2 |
| `f6d0a4b` | test(02-02): 5-test auth regression suite (AUTHFIX-01 + AUTHFIX-02) | Task 3 |
| `a409a3d` | docs(02-02): add AUTH_CONTRACT.md decision record (authfix-01, authfix-02) | Task 4 |

Outer-repo commit (this SUMMARY.md): created in the closing step of this plan.

## Tasks executed

| # | Name | Status | Notes |
|---|------|--------|-------|
| 1 | Add 400-on-/api/auth-validation handler in server.py + parity comment in routers/auth.py | done | Imports added (`RequestValidationError`, `JSONResponse`, `Request`); handler registered on app instance after `app = FastAPI(...)`; scoping by `request.url.path.startswith("/api/auth/")`; routers/auth.py gets a single AUTHFIX-02 comment (still unmounted, so no functional change there). |
| 2 | Create backend/tests/conftest.py | done | 93 lines, 7 fixtures (`base_url`, `admin_credentials`, `operator_credentials`, `viewer_credentials`, `admin_token`, `admin_headers`, `cleanup_audit_probe_users`); `cleanup_audit_probe_users` is `autouse=True, scope=session`; gracefully degrades when MongoDB unreachable. |
| 3 | Create backend/tests/test_auth_session.py | done | 140 lines; exactly 5 test functions matching the names mandated by the plan; AUTHFIX-01 and AUTHFIX-02 mentioned in docstrings (8 + 8 occurrences); CONS-auth-header cited (8 occurrences); zero inline credential literals. |
| 4 | Run regression suite + write AUTH_CONTRACT.md | done | 5/5 PASSED in 0.99s. AUTH_CONTRACT.md is 138 lines with all 7 required H2 sections (Status / Decisions / Verified contract / Code change / Frontend impact / Test runbook / Phase-3 follow-ups). Pre-commit hook initially blocked the doc commit because the runbook inlined `<TEST_ADMIN_PASSWORD>` literals — fixed by replacing literal-printing examples with `awk` extraction from gitignored `memory/test_credentials.md`; scanner now exits 0 on the post-fix tree. |

## Backend handler diff (verbatim — server.py)

The new handler block (registered AFTER `app = FastAPI(...)` and BEFORE `api_router = APIRouter(...)`):

```python
# ==================== AUTHFIX-02: VALIDATION ERROR HANDLER ====================
# CONS-auth-header (locked SPEC) requires HTTP 400 for malformed body on /api/auth/*.
# FastAPI's default for Pydantic ValidationError is HTTP 422 — we remap ONLY for
# /api/auth/* paths so other routes (vessels/COA/etc.) keep the standard 422 default.
# Decision record: pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md (D-AUTH-01).
@app.exception_handler(RequestValidationError)
async def auth_validation_handler(request: Request, exc: RequestValidationError):
    if request.url.path.startswith("/api/auth/"):
        return JSONResponse(
            status_code=400,
            content={"detail": exc.errors()},
        )
    # Fall through to FastAPI default for non-auth routes (preserve 422 elsewhere).
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
```

Imports added at the top of `server.py` (line 1-4):

```python
from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Query, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
```

Parity comment in `routers/auth.py` (head of file):

```python
# Authentication Router
# NOTE: AUTHFIX-02 — when this router is eventually mounted (Phase 7 UPGRADE-01),
# the `auth_validation_handler` registered on the FastAPI app instance in server.py
# will apply here automatically (it scopes by request.url.path startswith('/api/auth/')).
# No router-side handler is needed here. Decision record: docs/audit/AUTH_CONTRACT.md.
```

## Conftest fixtures created

| Fixture | Scope | Type | Purpose |
|---------|-------|------|---------|
| `base_url` | session | str | Resolves `REACT_APP_BACKEND_URL` (default `http://localhost:8013`) |
| `admin_credentials` | session | dict | `{email, password}` from `TEST_ADMIN_EMAIL` / `TEST_ADMIN_PASSWORD` env vars |
| `operator_credentials` | session | dict | Same shape, OPERATOR env vars |
| `viewer_credentials` | session | dict | Same shape, VIEWER env vars |
| `admin_token` | session | str | Live login → `access_token` |
| `admin_headers` | session | dict | `{"Authorization": f"Bearer {admin_token}"}` |
| `cleanup_audit_probe_users` | session, autouse | int | Pre-test deletion of `audit-probe-*` users; returns `deleted_count`; degrades gracefully when Mongo unreachable |

All fixtures use `pytest.skip(...)` when their backing env var is missing — CI-friendly when secrets are not provisioned.

## Regression suite results

Command (all secrets via env vars, no shell-history literals):

```
REACT_APP_BACKEND_URL=http://localhost:8013 \
TEST_ADMIN_EMAIL=… TEST_ADMIN_PASSWORD=… \
TEST_OPERATOR_EMAIL=… TEST_OPERATOR_PASSWORD=… \
TEST_VIEWER_EMAIL=… TEST_VIEWER_PASSWORD=… \
JWT_SECRET=… JWT_ALGORITHM=HS256 \
MONGO_URL=mongodb://localhost:27017 DB_NAME=pltu_tenayan_test_02_02 \
backend/.venv/bin/pytest backend/tests/test_auth_session.py -v --tb=short
```

Outcome — exit code **0**, **5 passed in 0.99s**:

| # | Test | Result | Status code asserted |
|---|------|--------|----------------------|
| 1 | `test_login_then_me_rehydrates_same_user` | **PASSED** | 200 (login) + 200 (/me) — same `id`, `email`, `role ∈ {admin,operator,viewer}` |
| 2 | `test_login_with_invalid_password_returns_401` | **PASSED** | 401 with `{"detail": ...}` body |
| 3 | `test_login_with_malformed_body_returns_400` | **PASSED** | 400 for three malformed shapes (missing field, bad email, empty body) |
| 4 | `test_me_without_token_returns_403` | **PASSED** | 403 (FastAPI HTTPBearer default; D-AUTH-02 disposition) |
| 5 | `test_me_with_expired_token_returns_401` | **PASSED** | 401 (expired JWT forged with `exp = now - 5min`) |

The expired-token test **executed and passed** (NOT skipped) because `JWT_SECRET` was provided via env var sourced from `backend/.env`. Documented in AUTH_CONTRACT.md "Test runbook" so future operators can reproduce.

### Live-curl verification probes (Task 1 acceptance)

| Probe | Expected | Actual |
|-------|----------|--------|
| `POST /api/auth/login` empty body | 400 | **400** ✓ |
| `POST /api/auth/login` bad creds | 401 | **401** ✓ |
| `POST /api/vessels` empty body (with valid JWT) | 422 (non-auth route, FastAPI default preserved) | **422** ✓ |

The 422-on-/api/vessels probe confirms the handler's path-prefix scoping is working correctly — only `/api/auth/*` is remapped.

## AUTH_CONTRACT.md

Path: `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md` (138 lines)

H2 sections (7, all required):
- Status
- Decisions (D-AUTH-01 + D-AUTH-02 table)
- Verified contract (post-fix) — 6-row status-code table with test citations
- Code change — verbatim handler + scoping rationale
- Frontend impact — explicitly notes no FE change required
- Test runbook — local-process invocation + VPS-targeted invocation; both source secrets from gitignored `memory/test_credentials.md` via `awk`, never inline
- Phase-3 follow-ups — DOCS-01 / API_REFERENCE.md updates required

## Audit-probe cleanup

The conftest cleanup runs against whatever `DB_NAME` env var points to. During this plan's test run, `DB_NAME=pltu_tenayan_test_02_02` (test DB), so the cleanup affected the throwaway test database only — **0 audit-probe users deleted from the test DB** (test DB started empty). The 3 audit-probe-* synthetic users from Phase-1 plan 01-04 still live in the production VPS `pltu_tenayan.users` collection and are out of scope for this plan (per system-reminder). Phase-5 ops audit can clean them up manually with the documented filter `{email: /^audit-probe-/}`.

## Test infrastructure choice (deviation from plan)

### [Rule 3 — Blocking] Local-process backend instead of VPS-targeted live backend

- **Found during:** Task 4 setup. The plan assumed the backend was already running at `localhost:8013`. On this host, port 8013 was not bound — the production backend lives at `103.150.197.225:8013` (remote VPS). The system-reminder explicitly forbids touching production data: *"prefer pytest + httpx TestClient hitting the FastAPI app in-process. Use a separate test database or mocked Mongo — never the production MongoDB."*
- **Fix:** Spun up a local uvicorn on `127.0.0.1:8013` against an isolated test database `pltu_tenayan_test_02_02` on the local Mongo (`mongodb://localhost:27017`). Bootstrapped admin/operator/viewer users via `/api/auth/register` calls (test DB started empty). Ran pytest against `http://localhost:8013`. Stopped the uvicorn and dropped the test DB after the run.
- **Why this satisfies plan intent:** The plan idiom (`requests.post(BASE_URL/...)`) is preserved verbatim — tests don't know whether they're hitting a live VPS or a local process. The 5 test names, signatures, and assertions are exactly as the plan specified. The contract is verified end-to-end including network/serialization layers.
- **Why this satisfies the system-reminder:** No write touched production data. Test DB is a separate Mongo namespace and was dropped at teardown. Live VPS backend was never invoked.
- **Files modified:** None outside the planned set; this is a methodology choice, not a code change.
- **Commit:** Not applicable (runtime methodology).

### [Rule 3 — Blocking] AUTH_CONTRACT.md test-runbook commit blocked by credential scanner

- **Found during:** Task 4 commit step.
- **Issue:** The first draft of AUTH_CONTRACT.md "Test runbook" section inlined literal `<TEST_ADMIN_PASSWORD>` / `<TEST_OPERATOR_PASSWORD>` / `<TEST_VIEWER_PASSWORD>` strings inside example shell scripts. The pre-commit hook installed by Plan 02-01 correctly blocked the commit with `FAIL [Admin-password-literal]`.
- **Fix:** Rewrote the runbook to source all passwords from gitignored `memory/test_credentials.md` via `awk` extraction (`awk '/^## Akun Admin$/,/^##/{ if(/Password:/){...} }'`). No literal credentials remain in the doc; scanner exits 0 on the post-fix tree.
- **Why this is correct:** The scanner is doing exactly what it was built to do (Plan 02-01 AUTHFIX-05). The doc now teaches the env-var sourcing pattern by example, which is more useful than printing throwaway literals.
- **Files modified:** `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md`.
- **Commit:** Included in `a409a3d`.

## Deviations from Plan

### Auto-fixed issues (covered above)

1. **[Rule 3 — Blocking] Test infrastructure: local-process backend** — see "Test infrastructure choice" section above.
2. **[Rule 3 — Blocking] AUTH_CONTRACT.md credential-scanner block** — see same section.

### Auth gates

None. The "auth gate" in this plan was the credential-scanner block (handled in-process; no human action required because the resolution is to use env-var sourcing, which is the plan's existing design).

## Self-Check: PASSED

- FOUND: `pltu-tenayan-full-backup/backend/server.py` — `RequestValidationError` import + `@app.exception_handler` + `request.url.path.startswith("/api/auth/")` (3/3 grep matches)
- FOUND: `pltu-tenayan-full-backup/backend/routers/auth.py` — `AUTHFIX-02` parity comment (1 grep match)
- FOUND: `pltu-tenayan-full-backup/backend/tests/conftest.py` (93 lines, 7 fixtures, autouse=1, os.environ=4, <TEST_ADMIN_PASSWORD>=0)
- FOUND: `pltu-tenayan-full-backup/backend/tests/test_auth_session.py` (140 lines, 5 test functions, AUTHFIX-0[12]=8, CONS-auth-header=8, <TEST_ADMIN_PASSWORD>=0)
- FOUND: `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md` (138 lines, 7 H2 sections, D-AUTH-01=1, D-AUTH-02=2)
- FOUND: inner-repo commits `34d4c3e`, `54ea64b`, `f6d0a4b`, `a409a3d` (all reachable via `git -C pltu-tenayan-full-backup log --oneline`)
- CONFIRMED: `pytest backend/tests/test_auth_session.py` exit 0, 5/5 PASSED in 0.99s
- CONFIRMED: `bash scripts/check_credentials.sh` exits 0 on the post-commit tree (167 files scanned, 16 exemptions)
- CONFIRMED: live-curl probes — 400 (auth empty body), 401 (auth bad creds), 422 (non-auth route preserves default)
- CONFIRMED: production VPS and `pltu_tenayan.users` untouched — all writes scoped to throwaway test DB which was dropped at teardown
