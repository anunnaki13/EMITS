# Phase 25 Patterns - Data Quality Monitor

Date: 2026-05-14

## Backend Patterns

| Concern | Pattern |
| --- | --- |
| Service boundary | Put rule evaluation in `backend/services/data_quality.py`; routers only handle auth/query/export response mapping. |
| Stable issues | Generate deterministic `key` values from `collection:type:record-key`. |
| Indonesian copy | Issue messages and suggested fixes should be Indonesian, following alerts/admin route style. |
| Severity | Use `critical`, `warning`, `info`; summary status is highest active severity. |
| Query safety | Use projection and bounded `limit`; avoid unbounded document materialization where aggregation can answer the check. |
| Export | Follow `backend/routers/admin.py` CSV export pattern using FastAPI `Response`. |
| Import previews | Extend existing preview payloads additively with `data_quality`; do not change existing `issues` arrays. |
| Dashboard/report caveats | Add compact `data_quality` fields to service payloads; do not remove current keys. |

## Frontend Patterns

| Concern | Pattern |
| --- | --- |
| Layout | Dense operational tool layout, consistent with `SettingsPage.js` and `RuntimeHealthPanel.js`. |
| Navigation | Add `/data-quality` as admin/operator route and sidebar item. |
| Cards | Use compact cards for severity counts; no nested cards. |
| Tables | Use stable row layout with wrapping text; no overlapping badges or action buttons. |
| Filters | Use select controls for module/severity and icon buttons for refresh/export. |
| Copy | Indonesian labels: "Kritis", "Perlu perhatian", "Sehat", "Saran perbaikan". |

## Testing Patterns

| Test Area | Pattern |
| --- | --- |
| Service | Seed isolated records with marker and call service directly. |
| API | Use existing backend lifecycle fixture and admin/operator auth headers. |
| Import preview | Use in-memory XLSX bytes as in `test_import_preview.py`. |
| Frontend | Run `npm run build`; allow pre-existing hook warnings if unchanged. |
