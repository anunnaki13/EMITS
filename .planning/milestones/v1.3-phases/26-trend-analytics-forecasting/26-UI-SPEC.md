# Phase 26 UI Spec - Trend Analytics & Forecasting

Date: 2026-05-14
Status: ready

## Surfaces

- Dashboard: existing `/dashboard` operational monitoring view.
- Management report: existing report page/tab in `frontend/src/pages/LaporanPage.js`.
- PDF/Excel exports from management report.

## Dashboard Layout Contract

Add one compact section near the operational monitoring cards:

- title: "Trend & Forecast"
- caveat callout when `sparse_data` or low confidence is true
- cards:
  - stock forecast / coverage days
  - arrival fulfillment movement
  - supplier risk movement
  - COA delta movement
  - dispute movement
- stock forecast mini-list for 7/14/30 day horizons

The section must fit dashboard density and avoid decorative layout.

## Management Report Layout Contract

Add trend content inside the existing management report flow:

- trend summary strip for stock, arrivals, quality, disputes
- stock forecast panel with burn assumption and expected arrivals
- supplier trend rows/cards with:
  - supplier
  - volume movement
  - timeliness movement
  - quality delta movement
  - dispute movement
  - risk label

## States

Healthy/full data:

- Show direction badges and values.

Sparse/partial data:

- Indonesian copy: "Data pembanding terbatas; tren ditampilkan sebagai indikasi awal."
- Do not hide cards, but mark confidence low.

No forecast:

- Indonesian copy: "Forecast stok belum bisa dihitung karena data pemakaian belum tersedia."

Loading/error:

- Use existing dashboard/report loading and error pattern.

## Export Contract

Excel:

- `Trend Analytics` sheet includes current, previous, delta, direction, confidence.
- `Supplier Trends` sheet includes supplier-level trend metrics.
- `Stock Forecast` sheet includes horizon, projected stock, projected coverage, burn assumption, expected arrivals.

PDF:

- Add compact "Trend & Forecast" section with metric rows and forecast summary.

Both exports must use the same filter scope as the on-screen management report.

## Visual Rules

- Compact operational density.
- No hero, decorative blobs, or nested cards.
- Use existing badge/card styles and lucide icons already present in the app.
- Long Indonesian text wraps inside cells/cards.
- Button and card text must not overlap on common desktop/tablet/mobile widths.

