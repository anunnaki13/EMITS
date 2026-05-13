# Phase 25 Context - Data Quality Monitor

Date: 2026-05-14
Status: planning
Source: user approved continuing without an extra discuss phase; context derived from roadmap, requirements, and current codebase.

## Phase Goal

Operators and admins need an in-app data-quality monitor that surfaces stale data, missing fields, duplicates, unrealistic values, and COA outlier deltas before dashboards, reports, or imports mislead operational decisions.

## Requirements Covered

- `DQ3-01`: System computes data quality checks for stale data, missing dates, duplicates, negative/unrealistic values, and COA outlier deltas.
- `DQ3-02`: Admin/operator can view a data quality summary and issue list with module, severity, source record, and suggested fix.
- `DQ3-03`: Dashboard and management reports include data-quality caveats when source data is incomplete or suspicious.
- `DQ3-04`: Import flows surface data-quality impact before commit when uploaded data would create warnings or critical issues.
- `DQ3-05`: Data quality results are exportable or auditable for management follow-up.
- `DQ3-06`: Tests cover clean, warning, and critical data-quality cases.

## Current Codebase Context

Useful existing patterns:

- `backend/routers/admin.py` already has admin-only paginated lists and CSV export for audit logs.
- `backend/routers/alerts.py` already computes rule-based operational issues with stable keys and Indonesian messages.
- `backend/routers/planning_data.py` already reports import preview issues for PO Batubara and Merit Order.
- `backend/services/coa_reconciliation.py` already validates combined COA workbook imports with severity-tagged issues.
- Phase 24 introduced service boundaries:
  - `backend/services/query_filters.py`
  - `backend/services/dashboard_metrics.py`
  - `backend/services/management_reports.py`
  - `backend/services/operational_advisor.py`

## UX Boundary

The monitor should be an operational work surface, not a marketing-style page.

Primary display:

- severity cards: critical, warning, info/healthy
- issue table/list with module, type, source record, field, message, suggested fix
- filters for module and severity
- recompute/refresh and export actions
- Indonesian empty/healthy state

Access:

- Admin and operator can view data-quality monitor.
- Export can be admin/operator unless existing role rules suggest admin-only during implementation.

## Compatibility Boundary

In scope:

- Add backend service and router for data-quality report/issues/export.
- Add frontend page and navigation.
- Add data-quality caveats to dashboard operational payload and management report payload.
- Add import-preview data-quality impact for PO/Merit and COA combined preview path.
- Add focused backend tests and frontend build verification.

Out of scope:

- ML anomaly detection.
- Historical trend analytics; that belongs to Phase 26.
- AI advisor narrative changes; that belongs to Phase 27 except consuming exposed caveats later.
- Blocking imports outright based on data quality unless existing import validation already blocks invalid payloads.

## Canonical References

- `.planning/REQUIREMENTS.md` — DQ3 requirements.
- `.planning/ROADMAP.md` — Phase 25 success criteria.
- `.planning/phases/24-backend-service-boundary-refactor/24-01-SUMMARY.md` — service boundary created in previous phase.
- `backend/routers/alerts.py` — rule-based issue pattern.
- `backend/routers/admin.py` — pagination/export/admin endpoint pattern.
- `backend/routers/planning_data.py` — import preview issue pattern.
- `backend/services/coa_reconciliation.py` — COA validation issue pattern.
- `frontend/src/pages/SettingsPage.js` and `frontend/src/components/RuntimeHealthPanel.js` — dense admin UI patterns.
