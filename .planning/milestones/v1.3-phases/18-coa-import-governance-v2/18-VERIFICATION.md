# Phase 18 Verification — COA Import Governance v2

Date: 2026-05-13
Verdict: PASS

## Requirement Verification

| Requirement | Status | Evidence |
|-------------|--------|----------|
| COAIMP-01 | PASS | `preview-combined` parses and stores preview without mutating `coa_reconciliation`; UI opens preview dialog for one-file upload. |
| COAIMP-02 | PASS | Preview response includes row count, coverage, date range, validation summary, and row-level issues. |
| COAIMP-03 | PASS | Preview detects duplicate shipments and computes inserted/updated/unchanged/removed-if-replace diff. |
| COAIMP-04 | PASS | Commit accepts explicit `merge` or `replace`; replace requires `confirm_replace_all=true`; UI exposes mode selection and replace checkbox. |
| COAIMP-05 | PASS | Commit writes `import_history` with actor, filename, mode, counts, validation summary, diff summary, before/after totals, and snapshot id. |
| COAIMP-06 | PASS | Commit preserves dispute history, notes, attachments, resolution fields, and existing umpire workflow state when workbook lacks equivalent data; replace risk is reported in preview. |

## Operational Verification

- Latest workbook: `Rekapitulasi CoA Loading, Unloading dan Lab Internal 2026 (Upd. Maret).xlsx`.
- Preview smoke: 754 incoming rows, 754 existing rows, 0 inserted, 0 updated, 754 unchanged, 0 removed-if-replace.
- Merge smoke after no-op diff: inserted 0, updated 0, unchanged 754, deleted 0, before_total 754, after_total 754.

## Residual Risk

- Legacy three-file upload and legacy direct combined endpoint still exist for compatibility; the production UI uses the governed combined-workbook preview flow.
- Rollback is admin-only and restores the full pre-import `coa_reconciliation` snapshot. Operators should run backup before destructive replace-all imports once Phase 19 runbooks are complete.
