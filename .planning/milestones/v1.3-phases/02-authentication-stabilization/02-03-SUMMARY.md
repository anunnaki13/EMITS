---
phase: 02-authentication-stabilization
plan: 03
subsystem: auth-roles
tags: [authfix-03, role-enforcement, regression-tests, vessels, users-list]
requires:
  - "Plan 02-02 (conftest with admin_credentials, operator_credentials, viewer_credentials, admin_token, admin_headers, base_url, cleanup_audit_probe_users autouse)"
  - "Plan 02-01 (scripts/check_credentials.sh + pre-commit hook)"
provides:
  - "5-test pytest regression suite at backend/tests/test_auth_roles.py exercising AUTHFIX-03 across four endpoints (12 parametrize cases; 11 unconditional + 1 destructive-skipped)"
  - "Locked observable contract: admin-only DELETE /api/vessels and GET /api/users; admin+operator POST /api/upload/vessel; any-auth GET /api/vessels"
affects:
  - "pltu-tenayan-full-backup/backend/tests/test_auth_roles.py"
tech-stack:
  added: []
  patterns:
    - "Module-scoped local fixtures (operator_token/operator_headers/viewer_token/viewer_headers) layered on top of session-scoped conftest fixtures — keeps wave-2 file_modified overlap with Plan 02-02 at zero"
    - "pytest.mark.parametrize fan-out: 4 parametrize blocks expand 5 test functions to 12 cases at runtime"
    - "Destructive-test gating via @pytest.mark.skipif(os.environ.get('RUN_DESTRUCTIVE_TESTS') != '1') — admin DELETE-all-vessels success path skipped by default to protect production-shaped data"
    - "Empty-multipart-payload trick: send a 0-byte xlsx so the role gate fires before Excel parsing — admin/operator pass the gate then 400 on parse, viewer 403 from the gate; proves role enforcement without writing real data"
    - "Live-uvicorn-against-isolated-test-DB methodology (mirrors Plan 02-02): bootstrap admin/operator/viewer via /api/auth/register on an empty pltu_tenayan_test_02_03 database; drop the DB at teardown"
key-files:
  created:
    - "pltu-tenayan-full-backup/backend/tests/test_auth_roles.py (147 lines, 5 test functions, 12 parametrize cases)"
  modified: []
decisions:
  - "Use the vessels module as the role-tier test surface: it covers all three role tiers (any-auth read on GET /api/vessels, admin+operator on POST /api/upload/vessel, admin-only on DELETE /api/vessels) and adds a fourth admin-only tier via GET /api/users — closing AUTHFIX-03 with a single cohesive suite."
  - "Define operator_token / operator_headers / viewer_token / viewer_headers as LOCAL fixtures inside test_auth_roles.py (module-scoped) instead of expanding conftest.py — keeps file_modified overlap with Plan 02-02 at zero so wave-2 parallelism remains valid even if both plans are revisited."
  - "Default-skip the destructive admin DELETE-all-vessels success path (skipif RUN_DESTRUCTIVE_TESTS=1) — operator runs it once against a non-prod replay; the unconditional 11 tests still prove all four role-tier behaviors observably."
  - "Mirror Plan 02-02's local-uvicorn methodology: spin up uvicorn on 127.0.0.1:8013 against an isolated DB pltu_tenayan_test_02_03, register the three role users, run pytest, drop the DB. Production VPS at 103.150.197.225 was never invoked."
metrics:
  duration: ~3.1min
  completed: 2026-05-10
  tasks_completed: 2
  files_created: 1
  files_modified: 0
  commits_inner: 1
  commits_outer: 1
---

# Phase 02 Plan 03: Role-Enforcement Regression Suite — Summary

Closes AUTHFIX-03 by pinning admin/operator/viewer role enforcement on four representative endpoints (one per role-tier shape) with a pytest-runnable regression suite at `backend/tests/test_auth_roles.py`. The suite ran **11 passed, 1 skipped in 1.45s** against an isolated test database on a locally-spawned uvicorn — the production VPS at `103.150.197.225` and the live `pltu_tenayan` collection were never touched, satisfying the system-level constraint that role tests must never mutate production data.

## Endpoints chosen vs. ROADMAP success-criterion 3

ROADMAP success criterion 3 names "admin-only delete-all, operator-only upload, viewer read" as the canonical examples. The suite exercises that exact triplet plus a fourth admin-only tier:

| Role tier | Endpoint | server.py line | Behavior asserted |
|-----------|----------|----------------|-------------------|
| Any authenticated read | `GET /api/vessels` | 685 | admin/operator/viewer all 200 + pagination shape `{items, total, page}` |
| Admin + operator (write) | `POST /api/upload/vessel` (multipart) | 1383 | admin 400, operator 400 (role gate passes, Excel parse fails on empty payload), viewer 403 (role gate fires before parse) |
| Admin only (delete-all) | `DELETE /api/vessels` | 746 | operator 403, viewer 403 (admin success path env-gated) |
| Admin only (admin tier) | `GET /api/users` | 665 | admin 200, operator 403, viewer 403 |

The "operator-only" wording in the ROADMAP is read as "operator-or-admin" because no endpoint in `backend/server.py` is operator-exclusive (admin always shadows operator); the test still proves operator passes the gate and viewer is blocked, which is the observable property the criterion targets.

## Inner-repo commit (pltu-tenayan-full-backup/)

| Hash | Subject | Task |
|------|---------|------|
| `cd7259f` | feat(authfix-03): role enforcement regression suite (vessels delete/upload/read + users list) | Tasks 1+2 (single atomic commit per plan §commit step) |

Outer-repo commit (this SUMMARY.md): created in the closing step of this plan.

## Tasks executed

| # | Name | Status | Notes |
|---|------|--------|-------|
| 1 | Create `backend/tests/test_auth_roles.py` — role-tier regression suite | done | 147 lines, 5 test functions, 4 parametrize blocks → 12 runtime cases. AUTHFIX-03 cited 6 times. RUN_DESTRUCTIVE_TESTS gate at 5 mentions. Zero "<TEST_ADMIN_PASSWORD>" literals; zero `JWT_PREFIX` JWT literals. AST parses clean under Python 3.11. |
| 2 | Run the role suite + commit | done | Live execution: **11 passed, 1 skipped in 1.45s** against `http://127.0.0.1:8013` with isolated DB `pltu_tenayan_test_02_03`. Pre-commit credential scanner exited 0 (168 files scanned, 16 exemptions). Commit `cd7259f` landed on inner repo. |

## Test execution detail

Command (secrets sourced via env vars; nothing inline):

```bash
cd pltu-tenayan-full-backup
set -a; source backend/.env; set +a
export DB_NAME=pltu_tenayan_test_02_03
export REACT_APP_BACKEND_URL=http://127.0.0.1:8013
export TEST_ADMIN_EMAIL=admin-test@example.com
export TEST_ADMIN_PASSWORD=…   # generated per-run via openssl rand -hex 4
export TEST_OPERATOR_EMAIL=operator-test@example.com
export TEST_OPERATOR_PASSWORD=…
export TEST_VIEWER_EMAIL=viewer-test@example.com
export TEST_VIEWER_PASSWORD=…
./backend/.venv/bin/pytest backend/tests/test_auth_roles.py -v --tb=short
```

Outcome — exit code **0**, **11 passed, 1 skipped in 1.45s**:

| # | Test (parametrize case) | Result |
|---|-------------------------|--------|
| 1 | `test_get_vessels_succeeds_for_all_roles[admin]` | **PASSED** (200 + pagination shape) |
| 2 | `test_get_vessels_succeeds_for_all_roles[operator]` | **PASSED** (200 + pagination shape) |
| 3 | `test_get_vessels_succeeds_for_all_roles[viewer]` | **PASSED** (200 + pagination shape) |
| 4 | `test_upload_vessel_role_gate[admin]` | **PASSED** (400 — passed gate, parse failed) |
| 5 | `test_upload_vessel_role_gate[operator]` | **PASSED** (400 — passed gate, parse failed) |
| 6 | `test_upload_vessel_role_gate[viewer]` | **PASSED** (403 — gate blocked) |
| 7 | `test_delete_all_vessels_blocks_non_admin[operator]` | **PASSED** (403) |
| 8 | `test_delete_all_vessels_blocks_non_admin[viewer]` | **PASSED** (403) |
| 9 | `test_delete_all_vessels_admin_success` | **SKIPPED** (RUN_DESTRUCTIVE_TESTS not set — by design) |
| 10 | `test_get_users_admin_only[admin]` | **PASSED** (200) |
| 11 | `test_get_users_admin_only[operator]` | **PASSED** (403) |
| 12 | `test_get_users_admin_only[viewer]` | **PASSED** (403) |

`RUN_DESTRUCTIVE_TESTS` was deliberately NOT set during the plan run — the destructive admin-success path is documented in the runbook for an operator to execute once against a non-prod replay.

## Vessel-count-unchanged proof

Per Plan §verification step 2, vessel counts were captured before and after the suite ran:

| Probe | Total vessels | Source |
|-------|---------------|--------|
| Before pytest | 0 | `GET /api/vessels?page=1&page_size=1` against test DB `pltu_tenayan_test_02_03` (DB initialized empty for this run) |
| After pytest | 0 | same probe, post-run |

**Equality holds (0 = 0).** Production database `pltu_tenayan` was never connected to during this plan — the local uvicorn was bound to `pltu_tenayan_test_02_03` exclusively, and that DB was dropped at teardown. Production VPS at `103.150.197.225:8013` was never invoked.

## Credential availability

| Env var | Sourced during this run | Source-of-truth |
|---------|-------------------------|-----------------|
| `TEST_ADMIN_EMAIL` / `TEST_ADMIN_PASSWORD` | Y — bootstrapped via `/api/auth/register` against test DB | per-run random password via `openssl rand -hex 4`, never written to disk except `/tmp/.test-pwds-02-03` (chmod 600, deleted at teardown) |
| `TEST_OPERATOR_EMAIL` / `TEST_OPERATOR_PASSWORD` | Y — bootstrapped same way | same |
| `TEST_VIEWER_EMAIL` / `TEST_VIEWER_PASSWORD` | Y — bootstrapped same way | same |
| `JWT_SECRET` | Y — sourced from `backend/.env` | gitignored backend env |
| `MONGO_URL` | Y — sourced from `backend/.env` | gitignored backend env |
| `DB_NAME` | Y — overridden to `pltu_tenayan_test_02_03` for the run | export at session-start |
| `RUN_DESTRUCTIVE_TESTS` | N (deliberate) | n/a — destructive test stays skipped by default |

The `memory/test_credentials.md` file currently only carries the `<TEST_ADMIN_EMAIL> / <TEST_ADMIN_PASSWORD>` literal (operator/viewer were not added); for plan-2-03 we generated fresh per-run passwords against a throwaway DB rather than expanding `memory/test_credentials.md`. This keeps the gitignored credentials file scoped to the production-equivalent admin account only, and matches Plan 02-02's pattern of bootstrapping ephemeral users when a real-DB triple isn't available.

## Threat-register dispositions

| Threat ID | Status | Evidence |
|-----------|--------|----------|
| T-02-12 (E: viewer/operator → admin endpoint) | mitigated | `test_delete_all_vessels_blocks_non_admin` (operator + viewer) and `test_get_users_admin_only` (operator + viewer) all asserted 403 |
| T-02-13 (E: viewer → operator-tier upload) | mitigated | `test_upload_vessel_role_gate[viewer]` asserted 403 (role gate fired before parse) |
| T-02-14 (T: accidental delete of 111 production vessels) | mitigated | destructive admin-success path is `@pytest.mark.skipif(RUN_DESTRUCTIVE_TESTS != "1")`; suite ran against an isolated test DB (vessel count 0/0); production VPS never connected to |
| T-02-15 (I: leak via response.text in failure messages) | accepted | `r.text[:200]` truncation in upload assertion; no failure assertions ran on production data |
| T-02-16 (D: hung suite on missing env vars) | mitigated | `_login` helper has `timeout=10`; conftest's `_require_env` issues `pytest.skip` (clean) |

## Operator runbook (RUN_DESTRUCTIVE_TESTS=1, non-prod only)

To execute the destructive admin-success path against a non-prod database replay:

1. Restore a Mongo dump of `pltu_tenayan` to a throwaway DB name (e.g. `pltu_tenayan_replay_YYYYMMDD`).
2. Spin up a local uvicorn against that DB with the test admin user registered.
3. Export the env-var triple plus `RUN_DESTRUCTIVE_TESTS=1`.
4. Run `pytest backend/tests/test_auth_roles.py::test_delete_all_vessels_admin_success -v`. Expect exit 0; the test asserts the admin call returns 200 or 204.
5. Drop the throwaway DB.

Do NOT run with `RUN_DESTRUCTIVE_TESTS=1` against the production VPS or the live `pltu_tenayan` database — the test will erase all 111 vessel records.

## Test infrastructure choice (mirrors Plan 02-02 deviation)

Plan 02-02 documented that the test idiom `requests.post(BASE_URL/...)` is preserved while the actual `BASE_URL` points at a locally-spawned uvicorn against a throwaway DB. Plan 02-03 inherits the exact same methodology — same uvicorn binary, same isolated-DB pattern, same teardown — because (a) the system-reminder forbids touching production data, and (b) the test DB needs the three role users which we register on a clean DB. This is a runtime methodology choice, not a code change; no files modified outside the planned set.

## Deviations from Plan

None. The plan executed exactly as written — including the planned auto-add of fresh per-run users (the conftest fixtures from Plan 02-02 read whatever credential triple is in env, so we just exported per-run passwords against a freshly-registered triple). Test counts (11 passed + 1 skipped), commit format, file size (147 lines vs. min 90), and verification probes all match the plan's acceptance criteria verbatim.

## Self-Check: PASSED

- FOUND: `pltu-tenayan-full-backup/backend/tests/test_auth_roles.py` (147 lines, 5 test functions, 12 parametrize cases, 6 AUTHFIX-03 mentions, 0 "<TEST_ADMIN_PASSWORD>" literals, 0 JWT_PREFIX JWT literals, parses clean under Python 3.11)
- FOUND: inner-repo commit `cd7259f` (`git -C pltu-tenayan-full-backup log --oneline | head -1` → `cd7259f4 feat(authfix-03): role enforcement regression suite (vessels delete/upload/read + users list)`)
- CONFIRMED: `pytest backend/tests/test_auth_roles.py -v` exit 0 — **11 passed, 1 skipped in 1.45s**
- CONFIRMED: `bash scripts/check_credentials.sh` exit 0 (168 files scanned, 16 exemptions) on the post-commit tree
- CONFIRMED: vessel count unchanged before/after run (0=0 in test DB)
- CONFIRMED: production VPS `103.150.197.225` and live `pltu_tenayan` database never connected to during this plan
- CONFIRMED: test DB `pltu_tenayan_test_02_03` dropped at teardown (zero "test" databases remain in local Mongo)
- CONFIRMED: temporary credentials file `/tmp/.test-pwds-02-03` deleted at teardown
