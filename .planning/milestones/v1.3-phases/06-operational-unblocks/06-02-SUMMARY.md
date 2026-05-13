---
phase: 06-operational-unblocks
plan: 02
subsystem: backend/smart-blending
tags: [smart-blending, aggregation, data-correctness, mongodb]
dependency_graph:
  requires: [06-01]
  provides: [OPS-01-data]
  affects: [/api/ai/quick/smart-stock, get_database_context()]
tech_stack:
  added: [tests/factories/smartstock.py, tests/factories/sumberpemakaian.py]
  patterns: [pymongo direct-aggregate unit test, Phase-4 factory pattern]
key_files:
  modified:
    - pltu-tenayan-full-backup/backend/server.py
  created:
    - pltu-tenayan-full-backup/backend/tests/test_smart_blending_data.py
    - pltu-tenayan-full-backup/backend/tests/factories/smartstock.py
    - pltu-tenayan-full-backup/backend/tests/factories/sumberpemakaian.py
decisions:
  - "Collapsed batubara+biomassa dual-field aggregation into single total_pemakaian (matches live schema — no split exists)"
  - "FIX 7 sort field changed from tanggal to date (canonical field from live probe)"
  - "or 0 coercion hotfix (Phase-5 CP2) preserved verbatim across all 4 sites"
metrics:
  duration: "~12 min"
  completed: "2026-05-11"
  tasks_completed: 2
  files_changed: 4
---

# Phase 06 Plan 02: Smart-Blending Data Correctness Summary

**One-liner:** 7 surgical server.py aggregation fixes replacing phantom fields (`$tonase`, `$batubara_mt`, `$biomassa_mt`, `$energy_mwh`) with live-schema canonical fields (`$total_penerimaan`, `$total_pemakaian`), plus 3 green regression tests.

## What Was Done

### Task 06-02-01: 7 Aggregation Field-Name Fixes

All 7 sites fixed per RESEARCH §Focus 2 table. Each fix confirmed via grep before edit (no line drift).

| Fix | Location | Before | After |
|-----|----------|--------|-------|
| 1 | `get_database_context()` smartstock projection | `source, supplier, cargo, tonase` | `date, total_penerimaan, suppliers` |
| 2 | `get_database_context()` sumberpemakaian projection | `tanggal, energy_mwh, batubara_mt, biomassa_mt, sfc` | `date, total_pemakaian, suppliers` |
| 3 | `get_database_context()` smartstock `$sum` | `"$sum": "$tonase"` | `"$sum": "$total_penerimaan"` |
| 4 | `get_database_context()` sumberpemakaian `$sum` | dual `$batubara_mt` + `$biomassa_mt` | single `$total_pemakaian` |
| 5 | `/api/ai/quick/smart-stock` smartstock `$sum` | `"$sum": "$tonase"` | `"$sum": "$total_penerimaan"` |
| 6 | `/api/ai/quick/smart-stock` sumberpemakaian `$sum` | dual `$batubara_mt` + `$biomassa_mt` | single `$total_pemakaian` |
| 7 | `/api/ai/quick/smart-stock` sumberpemakaian `$avg` | `avg_batubara/$batubara_mt` + `avg_energy/$energy_mwh` | `avg_pemakaian/$total_pemakaian`; sort field `tanggal` → `date` |

Phase-5 CP2 `or 0` coercion hotfix preserved at all 4 sites (22 total `or 0` occurrences in file, unchanged from before).

### Task 06-02-02: 3 Regression Tests

New file `tests/test_smart_blending_data.py`:
- `test_smartstock_sum`: seeds 3 docs (1000+2000+3000), asserts aggregate = 6000
- `test_sumberpemakaian_sum`: seeds 3 docs (500+700+900), asserts aggregate = 2100
- `test_smart_stock_endpoint`: seeds 2+2 docs, hits `/api/ai/quick/smart-stock`, asserts `current_stock != 0` and canonical key names

New factories `tests/factories/smartstock.py` and `tests/factories/sumberpemakaian.py` follow Phase-4 factory pattern (pymongo direct insert, `MONGO_TEST_DB_NAME` env guard).

**Test result:** `3 passed in 4.50s`

## Grep Gates (All Pass)

```
$tonase / $batubara_mt / $biomassa_mt / $energy_mwh in server.py = 0
$total_penerimaan count = 2 (>= 2 required)
$total_pemakaian count = 3 (>= 3 required)
or 0 count = 22 (>= 4 required)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] Downstream consumer keys updated alongside aggregation pipeline changes**
- Found during: Tasks 1 (Fix 4 + Fix 7)
- Issue: Changing `$sum/$avg` output key names required updating the `penerimaan/batubara_pakai/biomassa_pakai/avg_daily` consumer code in the same function
- Fix: Updated key lookups from `total_batubara/total_biomassa/avg_batubara` to `total_pemakaian/avg_pemakaian`; collapsed `current_stock = penerimaan - batubara_pakai - biomassa_pakai` to `current_stock = penerimaan - pemakaian`
- Files modified: server.py lines ~2413-2416, ~2898-2911
- Commit: 056713b

**2. [Rule 3 - Missing] Factory files did not exist**
- Found during: Task 2
- Issue: `tests/factories/smartstock.py` and `tests/factories/sumberpemakaian.py` referenced in plan had not been created in Phase 4 (no smartstock/sumberpemakaian tests existed then)
- Fix: Created both factories following Phase-4 merit_order factory pattern
- Files: tests/factories/smartstock.py, tests/factories/sumberpemakaian.py
- Commit: 056713b

## Data-Quality Caveat

Per RESEARCH Pitfall 5: live MongoDB data may still show `total_penerimaan = 0` on some smartstock documents due to an upstream Excel upload-parser artifact where "TOTAL PENERIMAAN (MT)" was mis-parsed as a supplier key. This is a data-quality issue, not a code-correctness issue. These fixes ensure the aggregation references the correct field; whether that field has non-zero values in live data depends on the upload-parser fix (outside Phase 6 scope).

## Commits

- `056713b` — `fix(06-02): 7 aggregation field-name fixes + 3 regression tests` (inner repo)

## Self-Check

- [x] server.py modified at 4 file changes (267 insertions, 20 deletions)
- [x] test_smart_blending_data.py exists with 3 test functions
- [x] factories/smartstock.py exists
- [x] factories/sumberpemakaian.py exists
- [x] Commit 056713b verified in git log
- [x] 3 passed, 0 failed

## Self-Check: PASSED
