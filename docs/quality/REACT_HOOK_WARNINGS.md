# React Hook Warning Register

Date: 2026-05-13
Scope: Phase 20 Dashboard Command Center v3

## Status

`npm run build` passes. The Phase 20 dashboard changes do not introduce a new `react-hooks/exhaustive-deps` warning.

The warnings below remain documented intentional exclusions for this phase. They are legacy bootstrapping effects in existing module pages. Resolving all of them safely requires page-by-page fetch callback normalization because several fetch functions close over auth headers, filters, tab state, pagination state, and toast handling. That work is intentionally separated from the dashboard command-center change to avoid broad behavioral churn.

## Current Warnings

| File | Line | Warning Scope | Phase 20 Decision |
|------|------|---------------|-------------------|
| `frontend/src/pages/AIIntelligencePage.js` | 99 | `fetchHistory`, `fetchQuickData` | Documented legacy effect; normalize in future AI page cleanup. |
| `frontend/src/pages/BargePage.js` | 57 | `fetchBarges` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/BiomassaPage.js` | 115 | `fetchBiomassa` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/COAReconciliationPage.js` | 220 | `fetchData`, `fetchImportHistory`, `fetchKPIs`, `fetchSupplierData`, `fetchTrendData` | Documented legacy COA dashboard effect; defer because it has multiple parallel loaders. |
| `frontend/src/pages/DisputeMonitorPage.js` | 118 | `fetchData` | Documented legacy dispute effect; normalize with dispute workflow cleanup. |
| `frontend/src/pages/LaporanPage.js` | 82, 86 | `fetchData`, `fetchSuppliers` | Documented legacy report effect; normalize during reports v2. |
| `frontend/src/pages/MeritOrderPage.js` | 101 | `fetchData` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/POBatubaraPage.js` | 126 | `fetchYearsData` | Documented legacy PO year-loader effect; normalize with arrival schedule cleanup. |
| `frontend/src/pages/SettingsPage.js` | 127 | settings loaders | Documented legacy admin settings effect; normalize in settings reliability pass. |
| `frontend/src/pages/SmartStockPage.js` | 99 | `fetchData` | Documented legacy stock effect; normalize with stock module cleanup. |
| `frontend/src/pages/SumberPemakaianPage.js` | 72 | `fetchData` | Documented legacy stock usage effect; normalize with stock module cleanup. |
| `frontend/src/pages/TruckingPage.js` | 57 | `fetchTrucking` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |
| `frontend/src/pages/VesselPage.js` | 58 | `fetchVessels` | Documented legacy CRUD effect; normalize with CRUD page hook pass. |

## Acceptance Notes

- Dashboard Command Center v3 uses `useCallback` with explicit dependencies for `getAuthHeader`, period, supplier, and mode.
- The production build remains deployable despite warnings.
- Future work should fix one page group at a time with regression checks for auth, pagination, filtering, and initial load behavior.
