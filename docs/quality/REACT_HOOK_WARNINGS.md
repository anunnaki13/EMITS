# React Hook Warning Register

Date: 2026-05-14
Scope: Phase 20 Dashboard Command Center v3, updated by Phase 23 Dashboard Drilldown Integration

## Status

`npm run build` passes. The Phase 20 dashboard changes do not introduce a new `react-hooks/exhaustive-deps` warning.

Phase 22 added `RuntimeHealthPanel` as a separate component with `useCallback`-backed runtime status loading. Phase 23 normalized the dashboard-drilldown destination loaders for COA, Dispute Monitor, PO Batubara, and Smart Stock while adding query-driven filter context.

The warnings below remain documented intentional exclusions for this phase. They are legacy bootstrapping effects in existing module pages. Resolving all of them safely requires page-by-page fetch callback normalization because several fetch functions close over auth headers, filters, tab state, pagination state, and toast handling.

## Current Warnings

| File | Line | Warning Scope | Phase 20 Decision |
|------|------|---------------|-------------------|
| `frontend/src/pages/AIIntelligencePage.js` | 99 | `fetchHistory`, `fetchQuickData` | Documented legacy effect; normalize in future AI page cleanup. |
| `frontend/src/pages/BargePage.js` | 57 | `fetchBarges` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/BiomassaPage.js` | 115 | `fetchBiomassa` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/LaporanPage.js` | 127, 131 | `fetchData`, `fetchSuppliers` | Documented legacy report effect; still intentionally deferred because the page has coupled fetch/export/pagination state. |
| `frontend/src/pages/MeritOrderPage.js` | 101 | `fetchData` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/SettingsPage.js` | 128 | settings loaders | Legacy bootstrap effect remains; Phase 22 runtime status loader is isolated in `RuntimeHealthPanel`. |
| `frontend/src/pages/SumberPemakaianPage.js` | 72 | `fetchData` | Documented legacy stock usage effect; normalize with stock module cleanup. |
| `frontend/src/pages/TruckingPage.js` | 57 | `fetchTrucking` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/VesselPage.js` | 58 | `fetchVessels` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |

## Acceptance Notes

- Dashboard Command Center v3 uses `useCallback` with explicit dependencies for `getAuthHeader`, period, supplier, and mode.
- RuntimeHealthPanel uses `useCallback` for its admin runtime status fetch and does not add a SettingsPage-level loader warning.
- Phase 23 dashboard-drilldown pages for COA, Dispute Monitor, PO Batubara, and Smart Stock no longer emit hook dependency warnings.
- The production build remains deployable despite warnings.
- Future work should fix one page group at a time with regression checks for auth, pagination, filtering, and initial load behavior.
