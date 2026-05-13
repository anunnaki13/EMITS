# Phase 23 Context - Dashboard Drilldown Integration

Date: 2026-05-14
Status: planning

## Phase Goal

Dashboard filters become real working context inside destination pages. When users click from the operational dashboard into stock, arrivals/PO, COA, dispute, or reports pages, those pages must read the dashboard query filters, apply them to visible data, and show clear navigation context.

## User Context

The dashboard is being repositioned around the main operational monitoring surfaces:

- monitoring stock batubara
- monitoring jadwal dan realisasi kedatangan bahan bakar
- monitoring dispute umpire batubara

Phase 20 already moved the dashboard toward those operational cards and already passes filter query parameters in drilldown URLs. Phase 23 finishes the next layer: destination pages must consume those filters, show active chips, provide reset actions, and let users return to the filtered dashboard state.

## Requirements Covered

- `DRILL3-01`: Dashboard query filters for period, supplier, mode, status are consumed by destination pages instead of only being passed in URLs.
- `DRILL3-02`: Stock, arrivals/PO, COA, dispute, report pages show active filter chips and reset actions when opened from dashboard cards.
- `DRILL3-03`: Clear Indonesian empty/partial-data states when filters return sparse results.
- `DRILL3-04`: Drilldowns preserve navigation context so users can return to originating filtered dashboard.
- `DRILL3-05`: Tests cover dashboard-to-destination drilldowns and filtered API payloads.

## Scope

In scope:

- Define one shared frontend drilldown query contract.
- Update dashboard links to include a clear source marker and enough query data to reconstruct the originating dashboard filters.
- Update destination pages to initialize filter state from query params.
- Add active filter chips and reset/back controls on destination pages.
- Add backend filter support where destination APIs currently ignore dashboard query context.
- Add focused backend tests for filtered payloads and run frontend build verification.

Out of scope:

- A full second redesign of the dashboard layout.
- New forecasting models, new optimization logic, or new executive analytics.
- Authentication/authorization changes.
- Production deployment changes.

## Query Contract

Canonical query parameters:

- `from=dashboard`: marks navigation context.
- `period`: `YYYY` or `YYYY-MM`.
- `supplier`: dashboard supplier label/value.
- `mode`: `vessel`, `barge`, `trucking`, or `biomassa`.
- `status`: destination-specific status when the card is status-scoped.
- `tab`: reports-specific destination tab.
- `date_from` and `date_to`: explicit date range override when present.

Period interpretation:

- `YYYY` maps to `YYYY-01-01` through `YYYY-12-31`.
- `YYYY-MM` maps to the first through last day of that month.
- Invalid or missing period must not break direct page visits.

Navigation:

- Destination pages build a return URL to `/dashboard` with the original `period`, `supplier`, and `mode`.
- Direct visits without `from=dashboard` should behave normally.
- Reset actions clear dashboard-derived filters while preserving the destination page route.

## Affected Frontend Files

- `frontend/src/pages/Dashboard.js`
- `frontend/src/pages/SmartStockPage.js`
- `frontend/src/pages/POBatubaraPage.js`
- `frontend/src/pages/COAReconciliationPage.js`
- `frontend/src/pages/DisputeMonitorPage.js`
- `frontend/src/pages/LaporanPage.js`
- New shared utility/component files under `frontend/src/utils/` and `frontend/src/components/`.

## Affected Backend Files

- `backend/routers/coa.py`
- `backend/routers/smart_stock.py`
- `backend/routers/planning_data.py`
- Existing reports code in `backend/routers/reports.py` is already partially aligned and should only be changed if required by tests.

## Existing Signals

Already present:

- `Dashboard.js` builds `drilldownParams` from selected `period`, `supplier`, and `mode`.
- `LaporanPage.js` already reads `tab`, `mode`, `period`, `supplier`, `date_from`, and `date_to` on initial load.
- `backend/routers/planning_data.py` already supports supplier filtering for `/api/po-batubara`.
- `backend/routers/reports.py` already supports management report filters.

Still missing:

- Stock, PO, COA, and dispute pages do not consistently initialize their visible filters from dashboard URL params.
- Filter chips/reset/back controls are missing or inconsistent.
- COA/dispute APIs need filtered payload support beyond the existing local page filters.
- Focused tests for dashboard-to-destination filtering are missing.

