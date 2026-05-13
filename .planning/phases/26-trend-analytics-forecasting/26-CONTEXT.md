# Phase 26 Context - Trend Analytics & Forecasting

Date: 2026-05-14
Status: planning
Source: user approved continuing; context derived from roadmap, requirements, Phase 24 service boundaries, Phase 25 data-quality caveats, and current codebase.

## Phase Goal

Dashboard and management reports should stop showing only static current-period numbers. Operators and managers need period-over-period context, supplier trend risk labels, and projected stock coverage so they can see whether stock, arrivals, COA deltas, and disputes are improving or worsening.

## Requirements Covered

- `TREND3-01`: Dashboard and reports compare current period to previous period for stock, arrivals, supplier performance, COA delta, and disputes.
- `TREND3-02`: Supplier trend cards show volume, timeliness, quality delta, and dispute trend with clear risk labels.
- `TREND3-03`: Stock forecast projects coverage using configurable burn assumptions and expected arrivals.
- `TREND3-04`: Trend charts degrade safely for sparse historical data with Indonesian explanation instead of misleading charts.
- `TREND3-05`: PDF and Excel exports include trend context matching the on-screen filter scope.

## Current Codebase Context

Phase 24 extracted dashboard/report logic into service modules:

- `backend/services/dashboard_metrics.py` builds dashboard operational payloads.
- `backend/services/management_reports.py` builds management report payloads and source slices.
- `backend/services/query_filters.py` centralizes period/date/supplier/mode helpers.

Phase 25 added:

- `backend/services/data_quality.py` with data-quality caveats.
- Additive `data_quality` fields on dashboard operational and management report payloads.
- A `/data-quality` UI route that can be consumed as caveat context.

Frontend surfaces:

- `frontend/src/pages/Dashboard.js` renders the operational monitoring dashboard.
- `frontend/src/pages/LaporanPage.js` renders management reports and owns PDF/Excel export.

## UX Boundary

Trend analytics should be operationally dense and should support the dashboard cleanup direction the user requested:

- primary display: stock trend/forecast, arrivals realization trend, supplier risk trend, COA delta trend, dispute trend
- supplier cards/rows: volume, timeliness, quality delta, dispute movement, risk label
- sparse data states: Indonesian caveat copy near the chart/card instead of fake confidence
- exports: trend context follows exactly the same filter scope as the report screen

Out of scope for this phase:

- AI narrative/prompt upgrades; Phase 27 will consume these fields.
- Large redesign of the entire dashboard layout; Phase 28 is reserved for broader UI/UX polish.
- Predictive ML. Forecast should be deterministic and explain its burn/arrival assumptions.

## Canonical References

- `.planning/REQUIREMENTS.md` - TREND3 requirements.
- `.planning/ROADMAP.md` - Phase 26 success criteria.
- `.planning/phases/24-backend-service-boundary-refactor/24-01-SUMMARY.md` - backend service boundary decision.
- `.planning/phases/25-data-quality-monitor/25-01-SUMMARY.md` - data-quality caveats available for partial/suspicious data.
- `backend/services/dashboard_metrics.py` - dashboard operational payload integration point.
- `backend/services/management_reports.py` - management report payload and export source integration point.
- `backend/services/query_filters.py` - date/supplier/mode helper pattern.
- `frontend/src/pages/Dashboard.js` - dashboard UI surface.
- `frontend/src/pages/LaporanPage.js` - management report UI and export surface.

