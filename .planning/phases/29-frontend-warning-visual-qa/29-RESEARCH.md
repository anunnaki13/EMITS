# Phase 29 Research

**Date:** 2026-05-14
**Scope:** Frontend hook warnings, visual smoke coverage, and warning budget enforcement.

## Current Warning Register

`docs/quality/REACT_HOOK_WARNINGS.md` documents eight legacy `react-hooks/exhaustive-deps` warnings:

| Page | Warning Scope |
|------|---------------|
| `AIIntelligencePage.js` | `fetchHistory`, `fetchQuickData` |
| `BargePage.js` | `fetchBarges` |
| `BiomassaPage.js` | `fetchBiomassa` |
| `MeritOrderPage.js` | `fetchData` |
| `SettingsPage.js` | settings loaders |
| `SumberPemakaianPage.js` | `fetchData` |
| `TruckingPage.js` | `fetchTrucking` |
| `VesselPage.js` | `fetchVessels` |

These warnings are safe to normalize with `useCallback` where fetch functions only close over auth headers and explicit filter state.

## Existing Patterns

- `RuntimeHealthPanel.js` already uses `useCallback` for fetch loading and a dependency-aware `useEffect`.
- Dashboard drilldown pages use route-level `data-testid` anchors that visual smoke can target.
- CRUD pages share a fetch-on-filter-change pattern: fetch function reads filters, effect calls fetch and resets page.
- `LaporanPage.js` already normalized fetch callbacks in Phase 28.

## Visual Smoke Strategy

Use Playwright for browser smoke because the requirement explicitly needs browser screenshot coverage. Tests should:

- Support both desktop and tablet profiles.
- Accept `VISUAL_SMOKE_BASE_URL` for local or deployed frontend.
- Authenticate with `VISUAL_SMOKE_TOKEN` or `VISUAL_SMOKE_EMAIL`/`VISUAL_SMOKE_PASSWORD`.
- Capture screenshots into Playwright output artifacts.
- Assert route-level anchors, page titles, primary controls/surfaces, non-empty body text, and no horizontal overflow.
- Detect obvious same-line text collisions by checking rendered text element bounding boxes.

## Risk Notes

- Playwright browser binaries may not be installed in every developer machine. The repo should include the test and script; runtime setup can install Chromium via Playwright when needed.
- Settings page fetch callbacks interact with audit filters. Initial page load should call an unfiltered audit fetch, while manual filter/export actions continue using current filter state.
- Build warning enforcement should compare hook warnings only, not bundle-size advisories or upstream dependency notices.
