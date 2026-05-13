# Phase 28 Context - Operator UI/UX Polish

Date: 2026-05-14
Status: planning
Source: user requested dashboard/UI/UX cleanup; context derived from roadmap, requirements, dashboard/report frontend, and hook warning register.

## Phase Goal

Monitoring and reporting workflows should be cleaner, faster, and more stable on desktop/tablet. The user specifically called out that the dashboard should be reorganized around core operational monitoring: stock batubara, schedule vs actual fuel arrivals, and dispute/umpire monitoring.

## Requirements Covered

- `UX3-01`: Dashboard, report, and control pages share cleaner layout patterns for filters, headers, badges, loading states, and empty states.
- `UX3-02`: Top workflows require fewer clicks for monitoring stock, arrivals, COA disputes, and report/advisor review.
- `UX3-03`: Common desktop and tablet layouts have stable dimensions with no overlapping text, controls, cards, or charts.
- `UX3-04`: Loading, error, empty, partial-data, and success states use consistent Indonesian copy.
- `UX3-05`: Legacy React hook warnings are reduced where safe or kept in the warning register with explicit rationale.

## Current Codebase Context

Primary surfaces:

- `frontend/src/pages/Dashboard.js` - operational dashboard with stock, arrivals, dispute, supplier risk, trend/forecast, charts.
- `frontend/src/pages/LaporanPage.js` - report management tab, trend analytics, AI advisor, export.
- `docs/quality/REACT_HOOK_WARNINGS.md` - warning register.

Recent payloads available:

- `operationalStats.data_quality`
- `operationalStats.trend_analytics`
- `managementReport.trend_analytics`
- `advisorReport.confidence`, `advisorReport.limitations`, `advisorReport.recommendation_groups`

## UX Boundary

This phase is polish, not a visual redesign from scratch.

In scope:

- Dashboard quick actions for primary monitoring workflows.
- Data-quality/partial-state callouts where interpretation risk matters.
- Stable compact card/table sizing in dashboard/report surfaces.
- Laporan fetch hook cleanup where safe.
- Warning register update after build.

Out of scope:

- New design system package.
- Mobile-native redesign.
- Rewriting every CRUD page hook warning.
- Changing backend response contracts.

## Canonical References

- `.planning/REQUIREMENTS.md` - UX3 requirements.
- `.planning/ROADMAP.md` - Phase 28 success criteria.
- `.planning/phases/26-trend-analytics-forecasting/26-01-SUMMARY.md` - trend dashboard/report UI.
- `.planning/phases/27-ai-advisor-v3/27-01-SUMMARY.md` - advisor UI and payload.
- `frontend/src/pages/Dashboard.js` - dashboard polish surface.
- `frontend/src/pages/LaporanPage.js` - report/advisor polish surface.
- `docs/quality/REACT_HOOK_WARNINGS.md` - hook warning register.

