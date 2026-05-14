---
phase: 04-test-suite-stabilization
plan: 01
subsystem: test-infrastructure
tags:
  - phase-04
  - test-infrastructure
  - conftest
  - ai-mock-seam
  - excel-fixtures
  - credential-hygiene
dependency_graph:
  requires:
    - phase-03 (server.py, .env contract, LOCAL_SETUP runbook)
    - phase-02 (conftest.py base, test patterns, CREDENTIAL_HYGIENE.md framework)
  provides:
    - Wave-0 test infrastructure for 04-02, 04-03, 04-04
    - AIClient Protocol seam for future OpenRouter migration
    - Per-session isolated test DB lifecycle on port 18013
    - 4 synthetic xlsx fixtures for upload tests
    - 8 factory modules for test data seeding
    - Sanitized test files — STAB-03 tail complete
  affects:
    - pltu-tenayan-full-backup/backend/server.py (MONGO_TEST_DB_NAME, AI injection)
    - pltu-tenayan-full-backup/backend/tests/conftest.py (extended)
    - pltu-tenayan-full-backup/scripts/check_credentials.sh (4 EXCLUDE entries removed)
tech_stack:
  added:
    - pytest-asyncio==0.24.0 (async test support)
    - app/ai/client.py AIClient Protocol (D-04)
    - app/ai/legacy_llm_wrapper.py LegacyLLMClientWrapper (D-04)
    - tests/fakes/ai_client.py FakeAIClient (D-05)
  patterns:
    - subprocess lifecycle with env injection (AI_FAKE=1, MONGO_TEST_DB_NAME)
    - Protocol-typed dependency injection via FastAPI Depends()
    - Factory pattern for deterministic test data seeding
    - Env-var seam for test/prod branching (AI_FAKE)
key_files:
  created:
    - pltu-tenayan-full-backup/backend/pytest.ini
    - pltu-tenayan-full-backup/backend/app/ai/client.py
    - pltu-tenayan-full-backup/backend/app/ai/legacy_llm_wrapper.py
    - pltu-tenayan-full-backup/backend/tests/fakes/ai_client.py
    - pltu-tenayan-full-backup/backend/tests/factories/ (8 modules)
    - pltu-tenayan-full-backup/backend/tests/helpers/pagination.py
    - pltu-tenayan-full-backup/backend/tests/helpers/jwt.py
    - pltu-tenayan-full-backup/backend/tests/fixtures/excel/ (4 xlsx + HEADER_VARIANTS.md + test_fixtures_valid.py)
    - pltu-tenayan-full-backup/backend/scripts/generate_test_fixtures.py
    - pltu-tenayan-full-backup/backend/tests/test_conftest_lifecycle.py
  modified:
    - pltu-tenayan-full-backup/backend/server.py (MONGO_TEST_DB_NAME patch + AIClient Depends on 2 endpoints)
    - pltu-tenayan-full-backup/backend/tests/conftest.py (extended with lifecycle + seed fixtures)
    - pltu-tenayan-full-backup/backend/requirements.txt (added pytest-asyncio==0.24.0)
    - pltu-tenayan-full-backup/backend/tests/test_dashboard_advanced.py (credential sanitization)
    - pltu-tenayan-full-backup/backend/tests/test_coa_reconciliation.py (credential sanitization + URL fix)
    - pltu-tenayan-full-backup/backend/tests/test_merit_order.py (credential sanitization)
    - pltu-tenayan-full-backup/backend/tests/test_po_batubara.py (credential sanitization)
    - pltu-tenayan-full-backup/scripts/check_credentials.sh (4 EXCLUDE entries removed)
    - pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md (4 entries marked CLEARED)
decisions:
  - "D-06 env-var seam (AI_FAKE=1) confirmed: app.dependency_overrides does NOT cross subprocess boundary; env-var injection is the correct structural answer for subprocess-based test backend."
  - "Port 18013 for test backend: PHASE4_TEST_PORT=18013 default protects live :8013 production backend."
  - "pytest.ini placed inside backend/ (co-located with tests it governs)."
  - "_seed_baseline_data seeds 3 merit_order docs (year=2024, month=1..3) to satisfy existing test_merit_order.py:71 and :314 assertions against empty test DB."
metrics:
  duration: 11min
  completed_date: "2026-05-11"
  tasks_completed: 3
  tasks_total: 3
  files_created: 26
  files_modified: 9
---

# Phase 04 Plan 01: Test Infrastructure — SUMMARY

**One-liner:** Wave-0 test infra — pytest.ini + AIClient Protocol + env-var AI_FAKE seam + subprocess backend lifecycle on port 18013 + 8 factory modules + 4 synthetic xlsx fixtures + STAB-03 credential sanitization complete.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | AI seam + server.py DB override + pytest.ini | e0ebb9c | app/ai/client.py, app/ai/legacy_llm_wrapper.py, tests/fakes/ai_client.py, server.py, pytest.ini |
| 2 | conftest lifecycle + factories + helpers + xlsx | f601537 | tests/conftest.py, tests/factories/ (8 mods), tests/helpers/, tests/fixtures/excel/ (4 xlsx) |
| 3 | Credential sanitization + scanner cleanup | 736e18a | 4 test files, check_credentials.sh, CREDENTIAL_HYGIENE.md |

## Verification Results

All Wave-0 acceptance criteria pass:

- `grep -c 'MONGO_TEST_DB_NAME' server.py` → 1
- `grep -c 'class AIClient' app/ai/client.py` → 1
- `grep -c 'Depends(get_ai_client)' server.py` → 2
- `grep -c 'class FakeAIClient' tests/fakes/ai_client.py` → 1
- `pytest tests/test_conftest_lifecycle.py -q` → 6 passed
- `pytest tests/fixtures/excel/test_fixtures_valid.py -q` → 5 passed
- `bash scripts/check_credentials.sh` → exits 0 (10 exemptions, 200 files)
- 4 xlsx fixtures: each ≤ 15 KB; shipment codes SHP-TEST-001..005 confirmed
- `grep -c 'def _backend_lifecycle' tests/conftest.py` → 1
- `grep -c 'TEST_DB_NAME.startswith' tests/conftest.py` → 1
- `grep -c 'PHASE4_TEST_PORT\|18013' tests/conftest.py` → 14
- `grep -l 'def make_' tests/factories/*.py | wc -l` → 8
- `grep -c 'def assert_pagination_shape' tests/helpers/pagination.py` → 1
- `grep -c 'def mint_expired_token' tests/helpers/jwt.py` → 1
- `grep -rn '<TEST_ADMIN_PASSWORD>' backend/tests/ | wc -l` → 0
- `grep -c 'CLEARED 2026-05-11' CREDENTIAL_HYGIENE.md` → 4

## Deviations from Plan

### Auto-fixed Issues

None required.

### Minor Implementation Notes

1. **D-06 amendment already applied:** CONTEXT.md D-06 wording was pre-amended on 2026-05-11 to reflect AI_FAKE env-var seam. No re-amendment needed.

2. **conftest BASE_URL default changed:** Changed from `http://localhost:8013` to `http://127.0.0.1:18013` (the Phase 4 test port) via `os.environ.setdefault()` before the module-level constant is set. This is an intentional change per plan instructions — tests that don't set `REACT_APP_BACKEND_URL` will now target the test backend, not production.

3. **test_po_batubara.py print/docstring sanitized:** The plan explicitly required removing `<TEST_ADMIN_PASSWORD>` from the file. One occurrence remained in a docstring and one in a `print()` call; both were sanitized to match the CREDENTIAL_HYGIENE.md scanner policy.

4. **pytest-asyncio installed but not in requirements at start:** Added `pytest-asyncio==0.24.0` to `requirements.txt` per plan's conditional instruction (package was absent). pytest.ini `addopts` updated with `--asyncio-mode=auto`.

## Threat Surface Scan

No new network endpoints added. AI seam uses env-var branching only; `FakeAIClient` imports zero network libraries. Production backend is isolated from test traffic by port 18013. No new threat flags beyond what is documented in the plan's threat register (T-cred-leak-01, T-stub-bypass-01, T-test-db-cross-contam-01, T-prod-backend-clobber-01, T-fake-ai-network-egress-01 — all mitigated).

## Known Stubs

None. All Phase 4 infrastructure components are fully wired.

## Self-Check: PASSED

All key files found:
- FOUND: pltu-tenayan-full-backup/backend/app/ai/client.py
- FOUND: pltu-tenayan-full-backup/backend/tests/conftest.py
- FOUND: pltu-tenayan-full-backup/backend/pytest.ini
- FOUND: pltu-tenayan-full-backup/backend/tests/fixtures/excel/vessel_minimal.xlsx
- FOUND: .planning/phases/04-test-suite-stabilization/04-01-SUMMARY.md

All 3 task commits verified in inner repo:
- e0ebb9c: Task 1 (AI seam + server.py + pytest.ini)
- f601537: Task 2 (conftest + factories + helpers + xlsx)
- 736e18a: Task 3 (credential sanitization)
