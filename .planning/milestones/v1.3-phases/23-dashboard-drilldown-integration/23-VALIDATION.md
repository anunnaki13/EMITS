# Phase 23 Validation Plan - Dashboard Drilldown Integration

Date: 2026-05-14
Status: planned

## Static Checks

```bash
python3 -m py_compile backend/routers/coa.py backend/routers/smart_stock.py backend/routers/planning_data.py backend/routers/reports.py
```

```bash
cd frontend && npm run build
```

## Focused Backend Tests

Add and run:

```bash
ops/scripts/pytest_with_local_credentials.sh tests/test_dashboard_drilldown_filters.py tests/test_dashboard_operational.py tests/test_management_reports.py -q
```

Expected coverage:

- PO Batubara supplier/period payloads.
- Smart stock supplier/date payloads.
- COA list/KPI/trend/supplier payloads scoped by dashboard filters.
- Dispute monitor status/supplier/date payloads.
- Management report filtered payloads still work.

## Frontend Verification

Build verification:

```bash
cd frontend && npm run build
```

Manual browser smoke:

1. Open dashboard with selected period/supplier/mode.
2. Click stock drilldown.
3. Verify active chips, filtered date range, reset, and dashboard return.
4. Repeat for PO, COA, dispute, and reports.
5. Open each destination directly with no query params and verify default behavior still works.

## Acceptance Checklist

- `DRILL3-01`: destination pages consume dashboard query filters.
- `DRILL3-02`: destination pages show active chips and reset action.
- `DRILL3-03`: Indonesian empty states appear for sparse filtered results.
- `DRILL3-04`: dashboard return preserves originating filter context.
- `DRILL3-05`: focused tests cover filtered payloads.

## Residual Risks

- Real production data may contain supplier label variants not present in seed/test data.
- Some destination metrics may be aggregated from partially normalized historical records.
- Frontend build may still report pre-existing hook warnings documented in `docs/quality/REACT_HOOK_WARNINGS.md`; Phase 23 must not add new warnings.

