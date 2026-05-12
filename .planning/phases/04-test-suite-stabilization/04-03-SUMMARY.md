---
phase: 04-test-suite-stabilization
plan: 03
subsystem: testing
tags:
  - phase-04
  - excel-upload
  - coa-reconciliation
  - happy-path
  - round-trip
  - pytest

dependency_graph:
  requires:
    - 04-01 (conftest lifecycle port 18013, 4 synthetic xlsx fixtures at tests/fixtures/excel/, 8 factories)
    - 04-02 (admin seed in _seed_baseline_data, pytest.ini pythonpath=.)
  provides:
    - TEST-04: 4 receipt-mode upload tests (vessel/barge/trucking/biomassa) with round-trip assertions
    - TEST-05: 5 COA reconciliation happy-path tests (kpis/trend/supplier-consistency/export-excel/export-pdf)
  affects:
    - pltu-tenayan-full-backup/backend/tests/test_upload_excel.py (new)
    - pltu-tenayan-full-backup/backend/tests/test_coa_reconciliation.py (extended)

tech_stack:
  added: []
  patterns:
    - "Parametrized upload tests across 4 receipt modes via pytest.mark.parametrize"
    - "Per-mode deterministic GCV expected values dict for fixture-driven assertions"
    - "Empty-DB tolerant happy-path pattern: tests pass even when collection is empty"
    - "Binary response testing pattern: assert Content-Type + len(r.content) > 0; never call r.json() on binary endpoints"

key_files:
  created:
    - pltu-tenayan-full-backup/backend/tests/test_upload_excel.py
  modified:
    - pltu-tenayan-full-backup/backend/tests/test_coa_reconciliation.py

key-decisions:
  - "Per-mode EXPECTED_GCV_ARB dict (Rule 1 fix): biomassa fixture has gcv_arb=3050.0 (biomass-realistic), not 4250.0 (coal). Plan hypothesis was incorrect for biomassa. Explicit per-mode dict eliminates the false assertion."
  - "Pre-existing test_get_coa_reconciliation_paginated failure documented as out-of-scope: it predates this plan and asserts data[total] > 0 against empty test DB. Not caused by this plan; not modified per plan instructions."
  - "5 new COA happy-path tests appended as module-level functions (not class methods) to leverage conftest admin_headers fixture and work against empty test DB."

requirements-completed:
  - TEST-04
  - TEST-05

duration: 5min
completed: "2026-05-11"
---

# Phase 04 Plan 03: Excel Upload + COA Reconciliation Tests — SUMMARY

**TEST-04 closed (4 upload + round-trip tests via parametrize over vessel/barge/trucking/biomassa fixtures) and TEST-05 closed (5 COA reconciliation happy-path tests for kpis/trend/supplier-consistency/export-excel/export-pdf, all empty-DB tolerant).**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-10T20:31:06Z
- **Completed:** 2026-05-10T20:36:14Z
- **Tasks:** 2
- **Files created:** 1 (test_upload_excel.py)
- **Files modified:** 1 (test_coa_reconciliation.py)

## Accomplishments

- Created `test_upload_excel.py` with one parametrized test covering all 4 receipt modes (vessel, barge, trucking, biomassa) plus a role-denial test for viewer attempting upload
- Each upload test POSTs the synthetic xlsx fixture to `/api/upload/<mode>`, asserts 200 + non-zero count, then GETs the list endpoint with `search=SHP-TEST-001` to verify the row persisted in MongoDB (round-trip)
- Extended `test_coa_reconciliation.py` with 5 new module-level happy-path tests that use the conftest `admin_headers` fixture and pass against an empty test DB
- Binary export tests (`export/excel`, `export/pdf`) assert Content-Type and `len(r.content) > 0` without calling `.json()` — following RESEARCH §11.7

## Task Commits

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create test_upload_excel.py — 4 upload + round-trip tests | 00a79d9 | tests/test_upload_excel.py (new) |
| 2 | Extend test_coa_reconciliation.py — 5 TEST-05 happy-path tests | 40c0f94 | tests/test_coa_reconciliation.py (extended) |

## Verification Results

### TEST-04: Upload + Round-trip (test_upload_excel.py)

```
4 passed, 1 skipped
```

| Mode | Upload | Round-trip | GCV ARB |
|------|--------|------------|---------|
| vessel | 200 + count=5 | SHP-TEST-001 found | 4250.0 verified |
| barge | 200 + count=5 | SHP-TEST-001 found | 4250.0 verified |
| trucking | 200 + count=5 | SHP-TEST-001 found | 4250.0 verified |
| biomassa | 200 + count=5 | SHP-TEST-001 found | 3050.0 verified |
| viewer role-deny | SKIPPED (TEST_VIEWER_EMAIL not set) | — | — |

### TEST-05: COA Reconciliation Happy-path (new tests in test_coa_reconciliation.py)

```
5 passed (test_coa_kpis_happy_path, test_coa_trend_happy_path,
          test_coa_supplier_consistency_happy_path,
          test_coa_export_excel_happy_path, test_coa_export_pdf_happy_path)
```

### Combined plan-level run

`pytest tests/test_upload_excel.py tests/test_coa_reconciliation.py -q`:
- 24 passed, 3 skipped, 1 pre-existing failure

The 1 failure (`TestCOAReconciliationList::test_get_coa_reconciliation_paginated`) is pre-existing — it asserts `data["total"] > 0` against the empty test DB. This was failing before this plan and is not caused by any change in this plan.

### Wave-2 regression

`pytest tests/test_auth_session.py tests/test_auth_roles.py tests/test_pagination_shape.py -q`:
- 24 passed, 9 skipped — no regressions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Biomassa gcv_arb expected value was 4250.0 but fixture has 3050.0**
- **Found during:** Task 1 (test_upload_then_round_trip execution)
- **Issue:** Plan specified gcv_arb=4250.0 as the deterministic value for all modes, but the biomassa_minimal.xlsx fixture was generated with biomass-realistic GCV values (3050.0 for the first row). The test assertion `abs(gcv - 4250.0) < 0.01` failed for the biomassa mode with `abs(3050.0 - 4250.0) = 1200.0`.
- **Fix:** Added `EXPECTED_GCV_ARB` dict mapping each mode to its actual fixture first-row GCV value: `{"vessel": 4250.0, "barge": 4250.0, "trucking": 4250.0, "biomassa": 3050.0}`. Test now asserts `abs(gcv - EXPECTED_GCV_ARB[mode]) < 0.01`.
- **Files modified:** `backend/tests/test_upload_excel.py`
- **Verification:** `pytest tests/test_upload_excel.py -q` → 4 passed
- **Committed in:** 00a79d9 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — incorrect expected value in test assertion)
**Impact on plan:** The fix is correct and necessary — biomass genuinely has lower calorific value than coal. The EXPECTED_GCV_ARB dict documents the actual deterministic values in the fixtures, making the test more precise and maintainable.

## Known Stubs

None. All test functions are fully wired with real HTTP assertions.

## Threat Flags

None. No new network endpoints introduced. Tests only consume existing endpoints. Binary export assertions protect against accidentally treating binary response as JSON (T-coa-export-leak-01 mitigation).

## Deferred Items

**Pre-existing failure — out of scope:**
- `TestCOAReconciliationList::test_get_coa_reconciliation_paginated` asserts `data["total"] > 0` against empty test DB. This was failing before this plan. The plan instructions say "DO NOT modify existing tests." This should be addressed in a separate test-maintenance plan (either seed COA data in `_seed_baseline_data` or change the assertion to tolerate empty DB).

## Self-Check: PASSED

Files verified:
- FOUND: /home/damnation/emits/pltu-tenayan-full-backup/backend/tests/test_upload_excel.py
- FOUND: /home/damnation/emits/pltu-tenayan-full-backup/backend/tests/test_coa_reconciliation.py

Commits verified in inner repo:
- 00a79d9: Task 1 (test_upload_excel.py)
- 40c0f94: Task 2 (test_coa_reconciliation.py extended)
