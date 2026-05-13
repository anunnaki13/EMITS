# Phase 23 Research - Dashboard Drilldown Integration

Date: 2026-05-14
Status: complete

## Codebase Findings

### Dashboard

`frontend/src/pages/Dashboard.js` already has the key upstream behavior:

- tracks `selectedPeriod`, `selectedSupplier`, and `selectedMode`
- builds `drilldownParams`
- uses `drilldownHref(path, extraParams)` for destination links
- links to stock, PO, reports, dispute monitor, and COA reconciliation pages

The missing piece is not URL generation itself. The gap is that destination pages do not yet treat those query params as operational filter state.

### Reports Page

`frontend/src/pages/LaporanPage.js` is the strongest existing frontend pattern:

- `getInitialReportState()` reads URL search params.
- `period`, `supplier`, and explicit dates influence report filter state.
- Filtered management report calls are already wired through `/api/reports/management`.

This page should be refined rather than rewritten:

- add shared drilldown chips/back/reset behavior
- keep direct page visits working
- avoid creating duplicate query parsing logic inside the page

### Smart Stock Page

`frontend/src/pages/SmartStockPage.js` currently has:

- `startDate` and `endDate` filters
- `/api/smart-stock?start_date=...&end_date=...`
- no query-param initialization
- no supplier/mode drilldown display

The page can consume `period` by converting it to a date range. If `supplier` is provided, backend support should filter rows/supplier summaries so the visible data matches the dashboard context.

### PO Batubara Page

`frontend/src/pages/POBatubaraPage.js` currently has:

- year/month state and lazy month loading
- `/api/po-batubara?year=...&month=...`
- no query-param initialization
- no supplier drilldown display

Backend `backend/routers/planning_data.py` already supports `supplier` on `/api/po-batubara`, so the frontend can pass it into month fetches.

### COA Reconciliation Page

`frontend/src/pages/COAReconciliationPage.js` currently has:

- `search`, `statusFilter`, `dateFrom`, and `dateTo`
- list endpoint calls with `search`, `status`, `date_from`, and `date_to`
- KPI/trend/supplier calls that are not consistently scoped by dashboard query filters

This page needs the largest alignment:

- initialize date range and status from dashboard params
- add supplier filter to frontend calls
- update backend COA endpoints to support supplier/date/status where missing
- keep KPI, trend, supplier consistency, and list data aligned

### Dispute Monitor Page

`frontend/src/pages/DisputeMonitorPage.js` currently has:

- `statusFilter`
- `/api/coa-reconciliation/dispute-monitor?umpire_status=...`
- no supplier/date query initialization

This page should accept dashboard context and pass it to the backend dispute endpoint.

### Backend

Existing useful patterns:

- `backend/server.py` generic list query helpers support supplier/date filtering for operational source endpoints.
- `backend/routers/planning_data.py` supports year/month/supplier/search on PO data.
- `backend/routers/reports.py` has period/supplier/date matching helpers for management reports.
- `backend/tests/test_dashboard_operational.py`, `backend/tests/test_management_reports.py`, and `backend/tests/test_coa_reconciliation.py` show current test style.

Likely backend changes:

- Add safe supplier/date/status filters to COA list, KPI, trend, supplier, and dispute endpoints.
- Add optional supplier filtering to smart stock without relying on unsafe dynamic Mongo field paths.
- Preserve existing default payloads when no drilldown filters are supplied.

## Recommended Implementation Shape

### Shared Frontend Utility

Create `frontend/src/utils/dashboardDrilldown.js` with helpers:

- `parseDashboardDrilldown(search)`
- `periodToDateRange(period)`
- `buildDashboardReturnUrl(filters)`
- `buildDrilldownChips(filters, options)`
- `stripDashboardParams(search, paramsToKeep)`

Reasons:

- avoids repeating URL parsing across five pages
- makes period conversion testable and predictable
- keeps destination pages focused on their existing filter state

### Shared UI Component

Create `frontend/src/components/DashboardDrilldownBar.js`:

- compact horizontal filter context bar
- Indonesian chip labels: `Periode`, `Supplier`, `Moda`, `Status`
- actions: `Kembali ke dashboard`, `Reset filter dashboard`
- only render when dashboard filters are active

### Destination Page Updates

Smart stock:

- initialize `startDate`/`endDate` from `period` or explicit dates
- pass `supplier` to `/api/smart-stock` when present
- show drilldown bar and filtered empty state

PO Batubara:

- initialize selected year/month from `period`
- pass `supplier` to `/api/po-batubara`
- auto-expand the selected year/month when opened from dashboard
- show drilldown bar and filtered empty state

COA reconciliation:

- initialize `dateFrom`, `dateTo`, `statusFilter`, and supplier context
- pass supplier/date/status to all aligned backend calls
- show drilldown bar and filtered empty state

Dispute monitor:

- initialize status/date/supplier from query
- pass filters to dispute endpoint
- show drilldown bar and filtered empty state

Reports:

- keep existing query initialization
- replace page-local drilldown display with shared bar
- reset dashboard filters through the shared URL helper

Dashboard:

- include `from=dashboard` in generated drilldown links
- initialize dashboard filters from URL params so return navigation restores context
- keep current card layout intact

## Risks And Mitigations

- Risk: query params break direct page loads.
  - Mitigation: parse defensively and only activate dashboard UI when recognized params exist.

- Risk: supplier filtering on nested stock payloads is inconsistent.
  - Mitigation: post-filter/shape smart-stock data in Python instead of building unsafe dynamic Mongo paths from user input.

- Risk: KPI and list counts diverge on COA.
  - Mitigation: reuse one backend filter builder across COA list/KPI/trend/supplier/dispute logic.

- Risk: React hook warnings increase.
  - Mitigation: use existing `useCallback`/dependency patterns and rerun frontend build.

## Verification Targets

- Backend focused tests for filtered PO, smart stock, COA, dispute, and report payloads.
- Frontend production build.
- Manual smoke path:
  - dashboard filter period/supplier/mode
  - click stock, PO, COA, dispute, reports
  - verify chips, filtered data, reset, and dashboard return URL

