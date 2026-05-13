# React Hook Warning Register

Date: 2026-05-14
Scope: Phase 29 Frontend Warning & Visual QA

## Status

`npm run build` passes with no current `react-hooks/exhaustive-deps` warnings.

Phase 29 normalized the remaining documented legacy fetch effects in:

- `frontend/src/pages/AIIntelligencePage.js`
- `frontend/src/pages/BargePage.js`
- `frontend/src/pages/BiomassaPage.js`
- `frontend/src/pages/MeritOrderPage.js`
- `frontend/src/pages/SettingsPage.js`
- `frontend/src/pages/SumberPemakaianPage.js`
- `frontend/src/pages/TruckingPage.js`
- `frontend/src/pages/VesselPage.js`

The production build still emits the standard Create React App bundle-size advisory, but that advisory is not a React hook warning and is outside this register.

## Current Warnings

No current React hook dependency warnings.

## Enforcement

Run the warning-budget gate from the frontend directory:

```bash
npm run build:checked
```

The gate runs `npm run build`, parses `react-hooks/exhaustive-deps` warnings, and compares them with this register. It fails when the build emits an undocumented hook warning or when this file contains a stale warning row.

## Acceptance Notes

- Dashboard, drilldown, report, runtime status, and CRUD loaders use dependency-aware fetch callbacks where currently touched.
- Settings page keeps initial audit loading on default filters while refresh/filter actions still use the selected audit filters.
- Future hook warnings must either be fixed in the same change or added to this register with file, line, owner, rationale, and follow-up path.
