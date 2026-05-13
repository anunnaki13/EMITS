# Phase 18 Summary — COA Import Governance v2

Date: 2026-05-13
Status: Complete

## Goal

Make recurring combined COA workbook updates previewable, validated, traceable, and rollback-safe before `coa_reconciliation` changes.

## Shipped

- Added COA import preview service logic in `backend/services/coa_reconciliation.py`.
- Added row metadata (`source_row`) for parsed combined workbook records.
- Added preview validation summary with critical/warning issues, duplicate detection, source coverage, date range, and before/after diff.
- Added preservation helper for local dispute workflow fields, notes, attachments, and umpire metadata.
- Added COA-specific endpoints in `backend/routers/coa.py`:
  - `POST /api/coa-reconciliation/preview-combined`
  - `GET /api/coa-reconciliation/import-preview/{preview_id}`
  - `POST /api/coa-reconciliation/import-preview/{preview_id}/commit`
  - `GET /api/coa-reconciliation/import-history`
  - `POST /api/coa-reconciliation/import-history/{history_id}/rollback`
- Added import snapshot storage in `coa_import_snapshots` for rollback.
- Added `COAImportCommitRequest` model.
- Updated `frontend/src/pages/COAReconciliationPage.js` so one-file combined workbook upload opens a preview dialog instead of immediately replacing data.
- Added import governance history cards with rollback action for admins.
- Added unit coverage for preview diff/duplicates/preservation.

## Notes

- Existing three-file legacy COA upload remains available for backward compatibility.
- Combined workbook UI now uses preview/commit flow.
- Runtime smoke against the March 2026 workbook parsed 754 rows and committed merge with 754 unchanged records.
