# React Hook Warning Register

Date: 2026-05-13
Scope: Phase 20 Dashboard Command Center v3, updated by Phase 22 Production Runtime & Observability

## Status

`npm run build` passes. The Phase 20 dashboard changes do not introduce a new `react-hooks/exhaustive-deps` warning.

Phase 22 adds `RuntimeHealthPanel` as a separate component with `useCallback`-backed runtime status loading. The existing SettingsPage bootstrap effect remains intentionally documented here because normalizing every legacy settings loader would be a broader settings reliability pass.

The warnings below remain documented intentional exclusions for this phase. They are legacy bootstrapping effects in existing module pages. Resolving all of them safely requires page-by-page fetch callback normalization because several fetch functions close over auth headers, filters, tab state, pagination state, and toast handling. That work is intentionally separated from the dashboard command-center change to avoid broad behavioral churn.

## Current Warnings

| File | Line | Warning Scope | Phase 20 Decision |
|------|------|---------------|-------------------|
| `frontend/src/pages/AIIntelligencePage.js` | 99 | `fetchHistory`, `fetchQuickData` | Documented legacy effect; normalize in future AI page cleanup. |
| `frontend/src/pages/BargePage.js` | 57 | `fetchBarges` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/BiomassaPage.js` | 115 | `fetchBiomassa` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/COAReconciliationPage.js` | 220 | `fetchData`, `fetchImportHistory`, `fetchKPIs`, `fetchSupplierData`, `fetchTrendData` | Documented legacy COA dashboard effect; defer because it has multiple parallel loaders. |
| `frontend/src/pages/DisputeMonitorPage.js` | 118 | `fetchData` | Documented legacy dispute effect; normalize with dispute workflow cleanup. |
| `frontend/src/pages/LaporanPage.js` | 119, 123 | `fetchData`, `fetchSuppliers` | Documented legacy report effect; still intentionally deferred after reports v2 UI expansion because the page has coupled fetch/export/pagination state. |
| `frontend/src/pages/MeritOrderPage.js` | 101 | `fetchData` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/POBatubaraPage.js` | 126 | `fetchYearsData` | Documented legacy PO year-loader effect; normalize with arrival schedule cleanup. |
| `frontend/src/pages/SettingsPage.js` | 128 | settings loaders | Legacy bootstrap effect remains; Phase 22 runtime status loader is isolated in `RuntimeHealthPanel`. |
| `frontend/src/pages/SmartStockPage.js` | 99 | `fetchData` | Documented legacy stock effect; normalize with stock module cleanup. |
| `frontend/src/pages/SumberPemakaianPage.js` | 72 | `fetchData` | Documented legacy stock usage effect; normalize with stock module cleanup. |
| `frontend/src/pages/TruckingPage.js` | 57 | `fetchTrucking` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/VesselPage.js` | 58 | `fetchVessels` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |

## Acceptance Notes

- Dashboard Command Center v3 uses `useCallback` with explicit dependencies for `getAuthHeader`, period, supplier, and mode.
- RuntimeHealthPanel uses `useCallback` for its admin runtime status fetch and does not add a SettingsPage-level loader warning.
- The production build remains deployable despite warnings.
- Future work should fix one page group at a time with regression checks for auth, pagination, filtering, and initial load behavior.
