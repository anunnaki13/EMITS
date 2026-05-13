---
phase: "05-collection-naming-debt-resolution"
plan: "02"
subsystem: "backend/server.py, scripts/migrate_collection_names.py, backend/tests/"
tags: [migration-script, server-py, collection-naming, phase-5, debt-02, debt-03, adr-009, adr-010, adr-011]
dependency_graph:
  requires: [05-01]
  provides: [05-03, 05-04]
  affects: [backend/server.py, scripts/migrate_collection_names.py, backend/tests/]
tech_stack:
  added: [migrate_collection_names.py (standalone pymongo CLI)]
  patterns: [idempotent-drop, pre-drop-count-guard, production-safety-guard, collection-checksum-md5]
key_files:
  created:
    - pltu-tenayan-full-backup/scripts/migrate_collection_names.py
    - pltu-tenayan-full-backup/backend/tests/test_migrate_collection_names.py
  modified:
    - pltu-tenayan-full-backup/backend/server.py
    - pltu-tenayan-full-backup/backend/tests/test_clean_checkout_gate.py
decisions:
  - "10 surgical token swaps applied to server.py (smart_stock→smartstock, sumber_pemakaian→sumberpemakaian, settings→app_settings) per ADR-009/010/011"
  - "Line 2377 `if module in [\"general\", \"smart_stock\"]:` preserved unchanged — Python routing key, not collection read"
  - "Migration script placed in scripts/ (not backend/) to avoid pytest auto-discovery (RESEARCH Pitfall 5)"
  - "Local variable `settings` retained after settings→app_settings token swap (minimal diff, RESEARCH Pitfall B)"
  - "Migration test fixture named test_db (matches plan verbatim code) — causes grep count of 6 not 5 but all 5 test behaviors present"
metrics:
  duration: "~9 min"
  completed_date: "2026-05-11T03:00:13Z"
  tasks_completed: 3
  files_changed: 4
---

# Phase 05 Plan 02: Surgical Server.py Edits + Migration Script + Regression Gate Summary

**One-liner:** 10 surgical token swaps closed DEBT-03 in server.py; idempotent pymongo migration script with 4 CLI flags and safety guards covers DEBT-02 (script half); 111 passed / 0 failed in full pytest suite (D-14 gate held).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 05-02-01 | Apply 10 surgical server.py edits (legacy → canonical) | `8d63cdd` | `backend/server.py` |
| 05-02-02 | Author `scripts/migrate_collection_names.py` | `fdd7bff` | `scripts/migrate_collection_names.py` |
| 05-02-03 | Write migration unit tests + DEBT-03 grep gate + regression bar | `00e81b1` | `backend/tests/test_migrate_collection_names.py`, `backend/tests/test_clean_checkout_gate.py` |

## Task 1: 10 Surgical server.py Edits (DEBT-03 Closed)

### Post-edit verification

```
$ grep -nE "db\.(smart_stock|sumber_pemakaian)\b|db\.settings\.find_one" backend/server.py
(empty — DEBT-03 closed)
```

### 10 edits applied (ADR → line → before → after)

| # | ADR | Line | Before | After |
|---|-----|------|--------|-------|
| 1 | ADR-009 | 2379 | `db.smart_stock.find(` | `db.smartstock.find(` |
| 2 | ADR-010 | 2387 | `db.sumber_pemakaian.find(` | `db.sumberpemakaian.find(` |
| 3 | ADR-009 | 2395 | `db.smart_stock.aggregate([` | `db.smartstock.aggregate([` |
| 4 | ADR-010 | 2398 | `db.sumber_pemakaian.aggregate([` | `db.sumberpemakaian.aggregate([` |
| 5 | ADR-011 | 2427 | `db.settings.find_one({"type": "coa"})` | `db.app_settings.find_one({"type": "coa"})` |
| 6 | ADR-009 | 2863 | `db.smart_stock.aggregate([` | `db.smartstock.aggregate([` |
| 7 | ADR-010 | 2868 | `db.sumber_pemakaian.aggregate([` | `db.sumberpemakaian.aggregate([` |
| 8 | ADR-010 | 2877 | `db.sumber_pemakaian.aggregate([` | `db.sumberpemakaian.aggregate([` |
| 9 | ADR-011 | 2926 | `db.settings.find_one({"type": "coa"})` | `db.app_settings.find_one({"type": "coa"})` |
| 10 | ADR-011 | 4346 | `db.settings.find_one({"type": "coa"})` | `db.app_settings.find_one({"type": "coa"})` |

**Line 2377 preserved:** `grep -c 'if module in ["general", "smart_stock"]' server.py` → 1 (unchanged Python routing key, not a collection read).

**py_compile:** `python3 -m py_compile backend/server.py` → exit 0.

## Task 2: Migration Script (`scripts/migrate_collection_names.py`)

**File:** `pltu-tenayan-full-backup/scripts/migrate_collection_names.py` (331 lines)

**CLI flags verified:**

```
$ python3 scripts/migrate_collection_names.py --help
usage: migrate_collection_names.py [-h] [--target-db DB_NAME] [--dry-run]
                                   [--apply] [--verify]
```

**Safety guard verified:**

```
$ DB_NAME="" python3 scripts/migrate_collection_names.py --dry-run
ERROR: Targeting production DB 'pltu_tenayan' requires explicit --target-db pltu_tenayan flag.
exit=1
```

**Idempotent SKIP output (test DB with no legacy collections):**

```
$ python3 scripts/migrate_collection_names.py --target-db pltu_tenayan_migration_dryrun --dry-run
[INFO] Connected to MongoDB: mongodb://localhost:27017
[INFO] Target DB: pltu_tenayan_migration_dryrun
[INFO] Mode: dry-run

[SKIP] smart_stock — does not exist (already clean or never created)
[SKIP] sumber_pemakaian — does not exist (already clean or never created)
[SKIP] settings — does not exist (already clean or never created)
[SKIP] ai_conversations — does not exist (already clean or never created)
exit=0
```

**LEGACY_TO_CANONICAL map (locked by Phase 5):**

```python
LEGACY_TO_CANONICAL = {
    "smart_stock":      "smartstock",       # ADR-009 / D-01
    "sumber_pemakaian": "sumberpemakaian",  # ADR-010 / D-02
    "settings":         "app_settings",     # ADR-011 / D-03
    "ai_conversations": "ai_chat_history",  # ADR-012 / D-04
}
```

## Task 3: Tests + Regression Bar (D-14)

**New test file:** `backend/tests/test_migrate_collection_names.py`

5 test behaviors (all passed):
1. `test_apply_drops_empty_legacy_collections` — Run 1: all 4 legacy empty collections dropped; canonical preserved
2. `test_apply_is_idempotent` — Run 2 on clean DB: no error, SKIP for each legacy name
3. `test_canonical_checksums_unchanged_by_apply` — DEBT-02 zero-data-loss: checksum BEFORE == AFTER
4. `test_halt_on_non_empty_legacy` — D-07: sys.exit(1) when legacy has > 0 docs (pytest.raises(SystemExit))
5. `test_dry_run_does_not_drop` — dry_run=True leaves all legacy collections intact

**Extended:** `backend/tests/test_clean_checkout_gate.py` + `test_no_legacy_collection_reads_in_server_py` (DEBT-03 grep gate with comment-line stripping for grep-gate hygiene).

**Phase-4 regression suite:**

```
111 passed, 13 skipped, 7 warnings in 39.88s
```

Previously 105 passed (Phase-4 baseline). 6 new tests added by Plan 05-02. Zero regressions. D-14 gate holds.

## Deviations from Plan

### Minor: grep count for test functions = 6 not 5

The plan's acceptance criteria expected `grep -c "^def test_" test_migrate_collection_names.py` to return 5. The fixture function is named `test_db()` (exactly as in the plan's verbatim code block), which the `^def test_` grep also matches, giving count=6. All 5 test behaviors from the plan are present and passing. This is a planning discrepancy in the acceptance criterion (the plan's own verbatim code produces 6 not 5). No fix applied — the 5 test behaviors are correctly implemented.

### Minor: whitespace cleanup in edits 6 and 9

Edits 6 and 9 also removed a trailing blank line while applying the context-anchor string for uniqueness. Net effect: one less blank line in two blocks (lines ~2864 and ~2925). No behavior change.

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. The migration script is a standalone operator tool that only accesses MongoDB on explicit invocation — it introduces no new trust boundary surface.

## Self-Check

- [x] `pltu-tenayan-full-backup/backend/server.py` modified — commit `8d63cdd` confirmed
- [x] `pltu-tenayan-full-backup/scripts/migrate_collection_names.py` created — commit `fdd7bff` confirmed
- [x] `pltu-tenayan-full-backup/backend/tests/test_migrate_collection_names.py` created — commit `00e81b1` confirmed
- [x] `pltu-tenayan-full-backup/backend/tests/test_clean_checkout_gate.py` extended — commit `00e81b1` confirmed
- [x] DEBT-03 closed: zero legacy reads in server.py
- [x] D-14 gate: 111 passed / 0 failed

## Self-Check: PASSED

## Next Plan

**05-03: MIGRATION_RUNBOOK.md** — Document the production cutover procedure (mongodump backup + `--apply --verify` run + post-migration smoke test). Depends on 05-02 deliverables (migration script exists, tested, idempotent).
