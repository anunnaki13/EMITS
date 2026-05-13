# Phase 28 Research - Operator UI/UX Polish

Date: 2026-05-14
Status: complete

## Implementation Findings

### Dashboard

The dashboard already has the right major cards after earlier phases:

- Monitoring Stock Batubara
- Jadwal vs Realisasi
- Dispute / Umpire
- Risiko Supplier
- Trend & Forecast
- Monitoring Jadwal Kedatangan

The next highest value polish is a quick action strip under the header so operators can jump directly to stock, PO, dispute, reports, and data quality without scanning the whole page.

Data-quality caveats already exist in the payload but are not visible on the dashboard. Showing a compact caveat reduces the risk of trusting stale or critical data.

### Reports

`LaporanPage.js` now owns:

- management report filters
- management report summary
- trend/forecast
- advisor confidence/groups
- PDF/Excel export

The page still emits `react-hooks/exhaustive-deps` warnings for `fetchData` and `fetchSuppliers`. This is now safe to normalize because the report page behavior is already covered by backend contracts and production build checks.

### Warning Register

`docs/quality/REACT_HOOK_WARNINGS.md` should be updated after build. If `LaporanPage.js` warnings are removed, the register should remove that row and keep remaining warnings documented.

## Recommended Implementation

- Add dashboard quick action strip with operational metrics and links.
- Add dashboard data-quality status callout linking to `/data-quality`.
- Add stable min-height/overflow treatment to dashboard operational cards and report advisor sections.
- Refactor `LaporanPage.js` fetch functions to `useCallback` and update effects.
- Update hook warning register after build.

## Risks And Mitigations

- Hook refactor could cause repeated fetch loops.
  - Keep dependencies explicit and run production build.

- Quick action strip could clutter dashboard.
  - Keep it compact and metric-driven, not explanatory.

- Data-quality callout could duplicate the dedicated monitor.
  - Show only compact top caveats plus link.

