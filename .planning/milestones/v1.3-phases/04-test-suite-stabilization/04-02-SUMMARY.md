---
phase: 04-test-suite-stabilization
plan: 02
subsystem: auth-tests + pagination-tests
tags:
  - phase-04
  - auth
  - pagination
  - jwt
  - adr-004
  - adr-008
dependency_graph:
  requires:
    - 04-01 (conftest lifecycle on port 18013, helpers/jwt.py, helpers/pagination.py, pytest.ini)
    - phase-02 (test_auth_session.py baseline, test_auth_roles.py)
  provides:
    - TEST-02: all 5 auth coverage paths named and individually runnable
    - TEST-03: parametrized pagination envelope assertion on 7 list endpoints
  affects:
    - pltu-tenayan-full-backup/backend/tests/test_auth_session.py (refactored)
    - pltu-tenayan-full-backup/backend/tests/conftest.py (admin seed added)
    - pltu-tenayan-full-backup/backend/pytest.ini (pythonpath added)
    - pltu-tenayan-full-backup/backend/tests/test_pagination_shape.py (new)
tech_stack:
  added: []
  patterns:
    - pytest.mark.parametrize across 7 list endpoints
    - shared helper pattern (assert_pagination_shape, mint_expired_token)
    - HTTP-based test DB seeding via /api/auth/register (no direct Mongo writes for users)
key_files:
  created:
    - pltu-tenayan-full-backup/backend/tests/test_pagination_shape.py
  modified:
    - pltu-tenayan-full-backup/backend/tests/test_auth_session.py
    - pltu-tenayan-full-backup/backend/tests/conftest.py
    - pltu-tenayan-full-backup/backend/pytest.ini
decisions:
  - "Admin user seeded via /api/auth/register on the test backend (HTTP call in _seed_baseline_data), not via direct Mongo insert, to stay consistent with the backend's own hashing logic."
  - "pytest.ini pythonpath = . added (Rule 1 auto-fix): without it, `from tests.helpers.*` imports at collection time raise ModuleNotFoundError because backend/ is not in sys.path by default."
metrics:
  duration: 7min
  completed_date: "2026-05-11"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 3
---

# Phase 04 Plan 02: Auth + Pagination Tests — SUMMARY

**One-liner:** TEST-02 closed (5 auth paths via mint_expired_token helper + admin seed) and TEST-03 closed (16 parametrized pagination envelope assertions across 7 list endpoints using assert_pagination_shape).

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Audit test_auth_session.py — replace inline JWT mint, seed admin | 4613dd5 | tests/test_auth_session.py, tests/conftest.py, pytest.ini |
| 2 | Create test_pagination_shape.py — 7 endpoint parametrize | 5ee5406 | tests/test_pagination_shape.py |

## Verification Results

### TEST-02: Auth Coverage (5 paths)

All 5 TEST-02 paths have named, individually-runnable test functions:

| Path | Function | File |
|------|----------|------|
| 1 — Login success | `test_login_then_me_rehydrates_same_user` | test_auth_session.py |
| 2 — Login failure | `test_login_with_invalid_password_returns_401` | test_auth_session.py |
| 3 — Role-denied | (parametrized 403 assertions) | test_auth_roles.py |
| 4 — Token-expired | `test_me_with_expired_token_returns_401` | test_auth_session.py |
| 5 — /me rehydrate | `test_login_then_me_rehydrates_same_user` | test_auth_session.py |

Acceptance criteria:
- `grep -c 'from tests.helpers.jwt import mint_expired_token'` → 1
- `grep -c 'jwt.encode('` → 0 (inline JWT minting fully removed)
- `grep -cE 'def test_(login|me)'` → 5 (≥4)
- `grep -c 'status_code == 403' tests/test_auth_roles.py` → 1

### TEST-03: Pagination Contract (7 endpoints)

All 7 list endpoints covered by `test_pagination_shape.py`:

| # | Endpoint | Envelope Test | Empty Test |
|---|----------|--------------|------------|
| 1 | /api/vessels | PASSED | PASSED |
| 2 | /api/barges | PASSED | PASSED |
| 3 | /api/trucking | PASSED | PASSED |
| 4 | /api/biomassa | PASSED | PASSED |
| 5 | /api/po-batubara | PASSED | PASSED |
| 6 | /api/merit-order | PASSED | PASSED |
| 7 | /api/coa-reconciliation | PASSED | PASSED |

Plus: `test_custom_page_size_round_trips` PASSED, `test_invalid_page_rejected` PASSED.

**Total: 16 passed in ~8s** (`pytest tests/test_pagination_shape.py -q`)

### Combined plan-level run

`pytest tests/test_auth_session.py tests/test_auth_roles.py tests/test_pagination_shape.py -q`:
- 24 passed, 9 skipped
- Skips: operator/viewer credential tests (env vars not set in memory/test_credentials.md); destructive DELETE test (RUN_DESTRUCTIVE_TESTS not set). Both are expected.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pytest `from tests.helpers.*` imports failed at collection time**
- **Found during:** Task 1 (test collection attempt)
- **Issue:** `ModuleNotFoundError: No module named 'tests'` — pytest did not add `backend/` to `sys.path` during collection, so `from tests.helpers.jwt import mint_expired_token` at the module level failed.
- **Fix:** Added `pythonpath = .` to `backend/pytest.ini` (pytest 7.0+ feature). This is equivalent to the `PYTHONPATH=str(BACKEND_DIR)` the conftest sets for the spawned subprocess, applied to the test collection process itself.
- **Files modified:** `backend/pytest.ini`
- **Commit:** 4613dd5

**2. [Rule 1 - Bug] Fresh test DB has no admin user — login-dependent auth tests fail with 401**
- **Found during:** Task 1 (first pytest run of test_auth_session.py)
- **Issue:** `test_login_then_me_rehydrates_same_user` fails with "Email atau password salah" (401) because the Phase-4 lifecycle fixture spawns a completely empty test DB. No admin user exists.
- **Fix:** Extended `_seed_baseline_data` in `conftest.py` to POST to `/api/auth/register` on the test backend (port 18013) using `TEST_ADMIN_EMAIL` / `TEST_ADMIN_PASSWORD` env vars. The registration is idempotent (HTTP 400 "already registered" → skip). This keeps the user hash consistent with the backend's bcrypt path.
- **Files modified:** `backend/tests/conftest.py`
- **Commit:** 4613dd5

### Minor Notes

1. `test_auth_roles.py` passes 3 tests (admin-only paths) and skips 9 (operator/viewer require env vars not in `memory/test_credentials.md`). This is expected behavior — the memory file only documents an admin account. TEST-02 path 3 (role-denied, 403) IS present in the file and will run when operator/viewer credentials are provided.

2. The `test_me_with_expired_token_returns_401` function signature changed: removed `admin_credentials` parameter (no longer needed after switching from inline jwt.encode to `mint_expired_token()`). The helper uses `JWT_SECRET` from env or the backend's hardcoded default, so no credentials fixture is required.

## Threat Surface Scan

No new network endpoints added. All test traffic goes to `http://127.0.0.1:18013` (isolated test backend). The admin user seeded via `/api/auth/register` goes into `pltu_tenayan_test_<sessionid>` which is dropped at session teardown. No new threat flags beyond what is documented in the plan's threat register (T-auth-bypass-01, T-token-replay-01, T-token-leak-via-log-01, T-pagination-shape-drift-01, T-page-size-injection-01 — all mitigated as designed).

## Known Stubs

None. All test functions are fully wired with real HTTP assertions against the live test backend.

## Self-Check: PASSED

Files verified:
- FOUND: /home/damnation/emits/pltu-tenayan-full-backup/backend/tests/test_pagination_shape.py
- FOUND: /home/damnation/emits/pltu-tenayan-full-backup/backend/tests/test_auth_session.py
- FOUND: /home/damnation/emits/pltu-tenayan-full-backup/backend/tests/conftest.py
- FOUND: /home/damnation/emits/pltu-tenayan-full-backup/backend/pytest.ini

Commits verified in inner repo:
- 4613dd5: Task 1 (auth session refactor + conftest seed + pytest.ini)
- 5ee5406: Task 2 (test_pagination_shape.py)
