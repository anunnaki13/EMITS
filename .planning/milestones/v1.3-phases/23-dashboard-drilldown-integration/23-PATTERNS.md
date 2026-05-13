# Phase 23 Patterns - Dashboard Drilldown Integration

Date: 2026-05-14
Status: complete

## Frontend Patterns To Reuse

### Dashboard Link Builder

File: `frontend/src/pages/Dashboard.js`

Use the existing `drilldownHref(path, extraParams)` pattern. Extend it with `from=dashboard` and keep it as the single place where dashboard filter context is attached to destination URLs.

### Query Initialization

File: `frontend/src/pages/LaporanPage.js`

`getInitialReportState()` is the closest existing pattern for reading query params into initial page state. Phase 23 should extract the shared pieces into `dashboardDrilldown.js` instead of cloning similar code across pages.

### Data Fetching With Hooks

Files:

- `frontend/src/pages/COAReconciliationPage.js`
- `frontend/src/pages/SmartStockPage.js`
- `frontend/src/pages/DisputeMonitorPage.js`

These pages already use stateful data fetching and loading states. Keep the same structure, but add query-derived state to the existing request params and dependency arrays.

### Existing Visual System

Use existing page headers, cards, buttons, badges, and table styles. The drilldown bar should feel like an operational filter toolbar, not a new decorative module.

## Backend Patterns To Reuse

### Safe Query Construction

File: `backend/server.py`

Generic source list endpoints already build date/supplier filters. Use similar defensive filtering and avoid raw user-provided regex unless escaped.

### Planning Data Filters

File: `backend/routers/planning_data.py`

`/api/po-batubara` already supports `year`, `month`, `supplier`, `search`, `page`, and `page_size`. Reuse this endpoint rather than creating a new one.

### Report Filter Helpers

File: `backend/routers/reports.py`

Management reports already use period/date/supplier filtering. Keep the same semantics for period interpretation so dashboard reports and destination pages do not disagree.

### COA Tests

File: `backend/tests/test_coa_reconciliation.py`

Follow existing test style and fixtures for COA/dispute payload tests.

## New Reusable Units

Expected additions:

- `frontend/src/utils/dashboardDrilldown.js`
- `frontend/src/components/DashboardDrilldownBar.js`
- `backend/tests/test_dashboard_drilldown_filters.py`

## Anti-Patterns To Avoid

- Parsing query strings separately in every page.
- Showing dashboard chips without actually filtering the API payload.
- Adding a new route for drilldowns when existing destination pages can own the behavior.
- Hiding all direct page content when no dashboard query exists.
- Adding broad dashboard redesign changes in this phase.

