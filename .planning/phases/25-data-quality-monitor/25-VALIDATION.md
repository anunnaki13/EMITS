# Phase 25 Validation - Data Quality Monitor

Date: 2026-05-14
Status: planned

## Required Verification

```bash
python3 -m py_compile backend/services/data_quality.py backend/routers/data_quality.py backend/services/dashboard_metrics.py backend/services/management_reports.py backend/routers/planning_data.py backend/routers/coa.py backend/server.py
```

```bash
ops/scripts/pytest_with_local_credentials.sh tests/test_data_quality.py tests/test_import_preview.py tests/test_coa_combined_workbook.py tests/test_dashboard_operational.py tests/test_management_reports.py -q
```

```bash
cd frontend && npm run build
```

## Functional Validation

- Seed clean, warning, and critical records in isolated DB.
- Verify service summary counts and severity status.
- Verify `/api/data-quality/summary`, `/api/data-quality/issues`, and `/api/data-quality/export`.
- Verify management report and operational dashboard include additive `data_quality` caveats.
- Verify PO/Merit import preview returns data-quality impact.
- Verify COA combined preview returns data-quality impact from existing validation issues.
- Verify frontend route renders summary cards, filters, issue rows, empty state, and export/refresh actions.

## Residual Risk To Watch

- Existing React hook warnings may remain; do not introduce new frontend warnings.
- Production collection scans should stay bounded and use projections/aggregation.
