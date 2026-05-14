---
phase: 04-test-suite-stabilization
plan: 04
subsystem: testing
tags:
  - phase-04
  - ai-mocked
  - dashboard
  - clean-checkout-gate
  - test-runner-docs
  - TEST-06
  - TEST-07
  - TEST-01

dependency_graph:
  requires:
    - phase: 04-test-suite-stabilization/04-01
      provides: FakeAIClient in tests/fakes/ai_client.py; AI_FAKE=1 lifecycle fixture; /tmp/emits-test-server.log sentinel
    - phase: 04-test-suite-stabilization/04-02
      provides: test_pagination_shape.py (Phase-4 test file required by gate)
    - phase: 04-test-suite-stabilization/04-03
      provides: test_upload_excel.py (Phase-4 test file required by gate)
  provides:
    - TEST-06 closed: test_ai_endpoints.py — LLM-calling endpoints mocked + 6 quick endpoints + LLM-budget-leak guard
    - TEST-07 closed: test_dashboard_advanced.py additions — /stats + /advanced happy-path with field assertions
    - TEST-01 closed: test_clean_checkout_gate.py — structural gate (file existence + collect-only)
    - Operator runbook: tests/TEST-RUNNER.md — single-page Phase-4 suite reference
  affects:
    - gsd-verifier (Phase 4 close-out verification)
    - Phase 5 (collection naming consolidation)

tech-stack:
  added: []
  patterns:
    - LLM-budget-leak guard via server-log grep (T-llm-budget-leak-01)
    - Structural acceptance gate via subprocess pytest --collect-only
    - Conftest fixture-based happy-path tests (base_url + admin_headers) for empty-DB tolerance

key-files:
  created:
    - pltu-tenayan-full-backup/backend/tests/test_ai_endpoints.py
    - pltu-tenayan-full-backup/backend/tests/test_clean_checkout_gate.py
    - pltu-tenayan-full-backup/backend/tests/TEST-RUNNER.md
  modified:
    - pltu-tenayan-full-backup/backend/tests/test_dashboard_advanced.py

key-decisions:
  - "Smart-blending response wraps AI JSON in ai_recommendation key (not top-level) — CONS-blending-ai-output keys asserted under body['ai_recommendation']"
  - "test_no_outbound_llm_calls_observed uses HTTP-call markers only (not legacy-ai-sdk module import) — module import occurs at server startup regardless of AI_FAKE"
  - "test_clean_checkout_gate uses subprocess pytest --collect-only (not full run) to avoid recursive lifecycle fixture spawn"
  - "Pre-existing failures (test_fuel_composition_donut, test_coa_reconciliation_paginated, test_merit_order, test_po_batubara) documented as carry-forward — not introduced by this plan"

requirements-completed:
  - TEST-06
  - TEST-07
  - TEST-01

duration: 6min
completed: "2026-05-11"
---

# Phase 04 Plan 04: AI Mocked + Dashboard + TEST-01 Gate — SUMMARY

**test_ai_endpoints.py (9 tests, TEST-06) + test_dashboard_advanced.py happy-path additions (TEST-07) + test_clean_checkout_gate.py structural gate (TEST-01) + TEST-RUNNER.md operator runbook; all 7 TEST-NN requirements now closed.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-10T20:42:39Z
- **Completed:** 2026-05-10T20:48:53Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- TEST-06 closed: 9 tests in test_ai_endpoints.py — FakeAIClient intercepts both LLM-calling endpoints (POST /api/ai/query + POST /api/smart-blending/recommend), 6 quick DB-only endpoints pass, LLM-budget-leak guard confirms zero outbound HTTP calls
- TEST-07 closed: 2 happy-path tests appended to test_dashboard_advanced.py — GET /api/dashboard/stats (10 DashboardStats fields) and GET /api/dashboard/advanced (10 analytics keys), both pass against empty test DB
- TEST-01 closed: 3 tests in test_clean_checkout_gate.py — Phase-4 file existence, Wave-0 deliverable existence, subprocess pytest --collect-only succeeds; TEST-RUNNER.md documents operator workflow

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_ai_endpoints.py** - `1bc3568` (feat)
2. **Task 2: Extend test_dashboard_advanced.py** - `5f551db` (feat)
3. **Task 3: TEST-01 structural gate + TEST-RUNNER.md** - `4a2de7b` (feat)

**Plan metadata:** [pending final commit]

## Files Created/Modified

- `pltu-tenayan-full-backup/backend/tests/test_ai_endpoints.py` — TEST-06: 9 tests covering 2 LLM-mocked endpoints + 6 quick DB-only endpoints + LLM-budget-leak guard
- `pltu-tenayan-full-backup/backend/tests/test_dashboard_advanced.py` — TEST-07: 2 new happy-path functions appended (test_dashboard_stats_happy_path + test_dashboard_advanced_happy_path)
- `pltu-tenayan-full-backup/backend/tests/test_clean_checkout_gate.py` — TEST-01: structural gate (3 tests)
- `pltu-tenayan-full-backup/backend/tests/TEST-RUNNER.md` — Operator runbook for Phase-4 suite

## LLM-Budget Assertion (T-llm-budget-leak-01)

Post-run grep of `/tmp/emits-test-server.log`:
- `generativelanguage.googleapis.com`: 0 matches
- `openrouter.ai/api`: 0 matches

AI_FAKE=1 wiring confirmed operational; FakeAIClient intercepted all LLM-calling endpoints.

## Smart-Blending Response Shape Note

The `/api/smart-blending/recommend` handler wraps the AI JSON output in an `ai_recommendation` key at the top level of the response. CONS-blending-ai-output keys (`recommendation`, `predicted_quality`, `meets_target`, `reasoning`) are asserted under `body["ai_recommendation"]`, not at `body` top level. This is consistent with the server.py return statement at line 3794.

FakeAIClient routing: `session_id = f"smart-blending-{uuid4()}"` at server.py:3770 contains "blend" — the FakeAIClient routes to BLENDING_JSON via session_id substring match (D-05). No test intervention needed.

## Decisions Made

1. Smart-blending CONS keys are under `body["ai_recommendation"]` — not top-level per plan template assumption. Corrected after reading server.py:3794.
2. `test_no_outbound_llm_calls_observed` excludes `legacy-ai-sdk.llm.chat` from markers because the module IS imported at server startup (server.py:2263) regardless of AI_FAKE=1 — only HTTP host markers are reliable LLM-call indicators.
3. Carry-forward documented rather than COA seeding (lower-risk for atomicity).

## Deviations from Plan

### Auto-fixed Issues

None - plan executed as written, with one clarification applied (smart-blending response wrapper key).

### Clarifications Applied (not deviations)

**1. Smart-blending response structure**
- **Found during:** Task 1 (test_ai_endpoints.py)
- **Issue:** Plan template showed CONS-blending-ai-output keys at top level; server.py:3794 wraps them under `ai_recommendation`
- **Fix:** Test asserts `body["ai_recommendation"]["recommendation"]` etc. (structurally correct)
- **Verification:** Test passes with exit 0

## Carry-Forward

**Pre-existing failures (not introduced by this plan):**

| Test | Failure Reason | Origin |
|------|----------------|--------|
| `test_fuel_composition_donut` | Asserts `len(fuel_comp) > 0` on empty test DB | Plan 04-01 baseline (pre-existing assertion) |
| `test_coa_reconciliation_paginated::data["total"]>0` | Empty test DB | Flagged in 04-03 SUMMARY |
| `test_merit_order::test_02..test_05,test_12` | DB expectations not met on empty test DB | Pre-existing from Phase 1 baseline |
| `test_po_batubara::test_get_po_batubara_by_year_month` | Empty test DB | Pre-existing from Phase 1 baseline |

**COA seeding (from 04-03 carry-forward):** Adding COA docs to `_seed_baseline_data` was scoped as optional. Lower-risk path chosen: document and defer to Phase 5 or 6 cleanup. The `test_coa_reconciliation_paginated::data["total"]>0` failure predates this plan.

## Phase 4 Close-Out Tally

All 7 TEST-NN requirements are now covered:

| Req | Description | Closed By |
|-----|-------------|-----------|
| TEST-01 | Structural acceptance gate | test_clean_checkout_gate.py (this plan) |
| TEST-02 | Auth (login, roles, 401/403) | test_auth_session.py + test_auth_roles.py (04-02) |
| TEST-03 | Pagination shape (7 endpoints) | test_pagination_shape.py (04-02) |
| TEST-04 | Excel upload + round-trip | test_upload_excel.py (04-03) |
| TEST-05 | COA reconciliation | test_coa_reconciliation.py (04-03) |
| TEST-06 | AI mocked (no LLM budget) | test_ai_endpoints.py (this plan) |
| TEST-07 | Dashboard happy-path | test_dashboard_advanced.py additions (this plan) |

## Full Suite Results (post-plan)

`cd pltu-tenayan-full-backup/backend && .venv/bin/pytest tests/ -q`: **96 passed, 10 failed (all pre-existing), 12 skipped**

## Threat Surface Scan

No new network endpoints introduced. All new test files are in `tests/` — not packaged in production. LLM-budget-leak mitigation wired in-suite. No new threat flags.

## Known Stubs

None. All test assertions use real server responses.

## Self-Check: PASSED

Files confirmed present:
- FOUND: pltu-tenayan-full-backup/backend/tests/test_ai_endpoints.py
- FOUND: pltu-tenayan-full-backup/backend/tests/test_clean_checkout_gate.py
- FOUND: pltu-tenayan-full-backup/backend/tests/TEST-RUNNER.md
- FOUND: pltu-tenayan-full-backup/backend/tests/test_dashboard_advanced.py

Task commits confirmed in inner repo:
- 1bc3568: Task 1 (test_ai_endpoints.py)
- 5f551db: Task 2 (test_dashboard_advanced.py)
- 4a2de7b: Task 3 (test_clean_checkout_gate.py + TEST-RUNNER.md)

---
*Phase: 04-test-suite-stabilization*
*Completed: 2026-05-11*
