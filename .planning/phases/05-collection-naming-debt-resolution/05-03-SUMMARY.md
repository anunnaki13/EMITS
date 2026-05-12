---
phase: "05-collection-naming-debt-resolution"
plan: "03"
subsystem: "pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md"
tags: [runbook, migration, rollback, phase-5, debt-02, debt-04]
dependency_graph:
  requires: [05-02]
  provides: [05-04]
  affects: [pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md]
tech_stack:
  added: []
  patterns: [operator-runbook, mongodump-backup, mongorestore-dryrun, rollback-two-path]
key_files:
  created:
    - pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md
  modified: []
decisions:
  - "MIGRATION_RUNBOOK.md placed at pltu-tenayan-full-backup/ top-level (sibling to LOCAL_SETUP.md) per RESEARCH Focus 7 placement decision and D-13"
  - "All 11 sections (0-10) written atomically in a single Write+commit; plan's two-task split was satisfied in one pass since full content was deterministically available from RESEARCH/CONTEXT/interfaces"
  - "4 [SKIP] lines as EXPECTED dryrun result explicitly documented per RESEARCH Pitfall 4 (legacy collections already absent from live pltu_tenayan DB)"
  - "Rollback documented as two separate sub-sections (§7a code-only vs §7b data-restore) per D-10"
metrics:
  duration: "~3 min"
  completed_date: "2026-05-11T03:06:25Z"
  tasks_completed: 2
  files_changed: 1
---

# Phase 05 Plan 03: MIGRATION_RUNBOOK.md Summary

**One-liner:** Operator runbook at `pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` (394 lines, 11 sections) documents the full Phase-5 production cutover: verbatim mongodump backup + dryrun namespace-remap + read-path deploy (cross-link to LOCAL_SETUP.md) + 48h observation checklist + pytest gate + legacy-drop + two-path rollback (git revert vs mongorestore --drop).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 05-03-01 | Author MIGRATION_RUNBOOK.md sections 0-6 | `5ba593b` | `MIGRATION_RUNBOOK.md` (394 lines, all 11 sections — 0-10 written atomically) |
| 05-03-02 | Sections 7-10 (Rollback / Cleanup / Cross-Refs / Retention) | included in `5ba593b` | same file — content was complete in the initial write |

## File: MIGRATION_RUNBOOK.md

**Path:** `pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md`
**Line count:** 394
**Inner-repo commit:** `5ba593b`

**Section list confirmed:**

```
## 0. Prerequisites
## 1. Backup Procedure (D-09)
## 2. Dryrun Procedure (D-12)
## 3. Read-Path Switch Deploy (D-06 steps 1-3)
## 4. Observation Window Checklist (>=48h, D-06 step 4)
## 5. pytest Regression Gate (D-14)
## 6. Legacy-Drop Procedure (D-06 step 5)
## 7. Rollback Procedure (D-10)
## 8. Cleanup Procedure (DEBT-05)
## 9. Cross-References
## 10. Backup Retention (D-11)
```

## Cross-Link Gates Passed

| Gate | Result |
|------|--------|
| `grep -c "LOCAL_SETUP.md"` >= 1 | 3 |
| `grep -c "TEST-RUNNER"` >= 1 | 3 |
| `grep -cE "ADR-009\|ADR-010\|ADR-011\|ADR-012"` >= 4 | 7 |
| `grep -c "05-04"` >= 1 | 1 |
| `grep -c "pltu_tenayan_migration_dryrun"` >= 3 | 7 |
| `grep -c "mongodump"` >= 2 | 6 |
| `grep -c "mongorestore"` >= 2 | 6 |
| `grep -c "migrate_collection_names"` >= 3 | 5 |
| `grep -cE "30[- ]?day"` >= 1 | 1 |
| `grep -cE "48[- ]?h\|48 hour"` >= 1 | 2 |
| `wc -l` >= 200 | 394 |
| All 11 sections present | PASS |

## Key Content Decisions

### §2 Dryrun — "4 [SKIP] lines is the EXPECTED result"

The runbook explicitly documents (per RESEARCH Pitfall 4) that when `migrate_collection_names.py --apply --verify` is run against `pltu_tenayan_migration_dryrun`, all 4 legacy collections (`smart_stock`, `sumber_pemakaian`, `settings`, `ai_conversations`) will report `[SKIP] — does not exist`. This is EXPECTED behavior — the live `pltu_tenayan` DB has never had these legacy collection names, so the dryrun copy won't either. An operator seeing 4 [SKIP] lines should proceed to §3, not be alarmed.

### §7 Rollback — Two Separate Paths

Per D-10, rollback is documented as two distinct sub-sections:

- **§7a Code-Only Rollback (most common):** `git revert <commit-hash>` on the Plan 05-02 feat commit + LOCAL_SETUP.md §VPS Service Recovery. Use when the code deploy caused a regression before any `--apply` ran. No data touch required.
- **§7b Full Data Restore (extreme edge case):** `mongorestore --drop --uri ... --nsInclude 'pltu_tenayan.*' "$BACKUP_DIR"`. Use ONLY if a canonical collection lost data after `--apply` ran. Per D-08, the legacy collections were empty at drop time so this path should never be needed. Includes WARNING block about data loss from writes between backup and restore time.

### §3 Smoke-Test — AI Module Behavioral Change

The runbook notes that post-deploy, `/ai/quick/smart-stock` will return real data (207 records, non-zero `total_penerimaan`) and `potential_loss` in `/ai/quick/coa-alerts` may change (uses real `price_per_kcal_per_ton` from `app_settings` instead of hardcoded 50). Both are positive consequences of ADR-009 + ADR-011, documented in the operator handoff note.

## Deviations from Plan

### Minor: Both tasks (05-03-01 and 05-03-02) completed in a single atomic write

The plan's two-task structure (§0-6 in Task 1, §7-10 in Task 2 via Edit append) was designed to produce two separate commits. Since all content was deterministically available from the plan's `<interfaces>` block, RESEARCH.md verbatim commands, and the existing migration script CLI, all 11 sections were written in a single atomic Write call and committed as `5ba593b`. No Edit append was needed. The plan's intent — producing a complete, verified runbook — is satisfied; the only deviation is the commit count (1 vs 2). Task 05-03-02's acceptance criteria are met by the single commit.

## Plan Dependencies

- **Requires:** 05-02 — migration script `scripts/migrate_collection_names.py` must exist and its CLI flags (`--target-db`, `--dry-run`, `--apply`, `--verify`) must be as documented. CLI verified live in 05-02-SUMMARY.md Task 2.
- **Blocks:** 05-04 — Plan 05-04 (production cutover, `autonomous: false`) reads this runbook step-by-step. The §6 Legacy-Drop and §8 Cleanup pointer (→05-04) sections are the handoff points.

## DEBT-02 + DEBT-04 Status

| Debt | Description | Status |
|------|-------------|--------|
| DEBT-02 | Dryrun procedure documented (documentation half) | CLOSED — §2 Dryrun Procedure with verbatim mongodump → mongorestore --nsFrom/--nsTo → migrate_collection_names.py --apply --verify commands |
| DEBT-04 | Rollback path documented + backup retention policy | CLOSED — §1 Backup + §7 Rollback (both paths) + §10 Retention (30-day policy) |
| DEBT-02 (execution half) | Actual mongodump backup taken on VPS | OPEN — operator-driven via Plan 05-04 §1 checkpoint |
| DEBT-04 (execution half) | --apply run on production DB | OPEN — operator-driven via Plan 05-04 §6 checkpoint |

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. MIGRATION_RUNBOOK.md is a static markdown documentation file. The threat mitigations from the plan's `<threat_model>` are addressed:

- **T-rollback-failure-01:** Both rollback paths (§7a `git revert`, §7b `mongorestore --drop`) documented separately with verbatim commands and explicit when-to-use guidance.
- **T-typo-targets-production-on-dryrun-01:** Dryrun target is always `pltu_tenayan_migration_dryrun`; typos create a new DB instead of damaging production. Script safety guard documented.
- **T-credentials-in-runbook-01:** No credentials inlined; cross-link to TEST-RUNNER.md §One-time setup + awk-pattern from LOCAL_SETUP.md.
- **T-premature-drop-by-operator-01:** §4 observation window checklist (5 items) must be passed before §6; §6's first command is `--dry-run` not `--apply`.

## Self-Check

- [x] `pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` created — commit `5ba593b` confirmed
- [x] 394 lines (>= 200)
- [x] 11 sections (0-10) present
- [x] All cross-link gates passed
- [x] DEBT-02 documentation surface closed
- [x] DEBT-04 documentation surface closed

## Self-Check: PASSED

## Next Plan

**05-04: Production Cutover** — `autonomous: false` plan. Follows this runbook step-by-step with operator checkpoints at §1 (backup confirmation), §3 (deploy confirmation), §6 (legacy-drop confirmation), and §8 (DATABASE_SCHEMA.md cleanup).
