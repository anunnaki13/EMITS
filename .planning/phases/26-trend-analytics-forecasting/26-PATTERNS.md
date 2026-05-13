# Phase 26 Patterns - Trend Analytics & Forecasting

Date: 2026-05-14

## Backend Patterns

| Concern | Pattern |
| --- | --- |
| Service boundary | Put current-vs-previous and forecast logic in `backend/services/trend_analytics.py`; routers remain unchanged. |
| Additive contracts | Add `trend_analytics` to dashboard operational and management report payloads; do not rename/remove existing keys. |
| Date filtering | Reuse `period_bounds`, `date_match`, `period_match`, `supplier_match`, `mode_match`, and `merge_match` from `query_filters.py`. |
| Sparse data | Return `sparse_data`, `confidence`, `source_counts`, and Indonesian `caveats` instead of fake chart data. |
| Metric deltas | Each metric returns current/previous/delta/delta_percent/direction/status/label. |
| Forecast | Use deterministic burn/arrival assumptions; include `assumptions` and `horizons`. |
| Supplier trends | Supplier rows include volume, timeliness, quality delta, dispute direction, and risk label. |
| Tests | Seed isolated current and previous periods; assert contract shape and sparse-data fallback. |

## Frontend Patterns

| Concern | Pattern |
| --- | --- |
| Dashboard | Add compact operational section, not a hero or marketing layout. |
| Report UI | Add trend summary and supplier trend table under existing management report. |
| Cards | Use existing card/badge style; avoid nested cards. |
| Copy | Indonesian labels: "Naik", "Turun", "Stabil", "Data pembanding terbatas", "Forecast stok". |
| Exports | Build PDF/Excel rows from `managementReport.trend_analytics`, preserving current filter scope. |
| Responsive | Keep trend cards in wrapping grid; supplier trend rows must wrap on mobile/tablet. |

## Verification Patterns

| Test Area | Pattern |
| --- | --- |
| Service | Directly test `build_trend_analytics` with seeded DB records. |
| Dashboard | Existing dashboard operational endpoint should include additive `trend_analytics`. |
| Reports | Existing management report endpoint should include additive `trend_analytics`. |
| Sparse | Test insufficient previous-period records returns `sparse_data: true` and Indonesian caveat. |
| Frontend | Run `npm run build`; keep pre-existing hook warnings documented. |

