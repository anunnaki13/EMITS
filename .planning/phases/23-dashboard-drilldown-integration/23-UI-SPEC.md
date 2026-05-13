# Phase 23 UI Spec - Dashboard Drilldown Integration

Date: 2026-05-14
Status: approved for implementation

## UI Goal

Destination pages must make dashboard context visible and actionable. A user who clicks from a filtered dashboard should immediately understand which operational filter is active, see filtered data, and have a clear way to return or clear that context.

## Pages Covered

- Smart Stock
- PO Batubara
- COA Reconciliation
- Dispute Monitor
- Laporan

## Shared Drilldown Bar

Create a reusable component, expected path:

- `frontend/src/components/DashboardDrilldownBar.js`

Placement:

- Below the destination page title/header controls.
- Above the page-specific data/filter area.
- Use an un-nested compact band or toolbar; do not place a card inside another card.

Display conditions:

- Render only when there is at least one dashboard-derived filter or `from=dashboard`.
- Direct page visits without dashboard params must not show unnecessary chrome.

Content:

- Short label: `Filter dashboard aktif`
- Chips:
  - `Periode: <value>`
  - `Supplier: <value>`
  - `Moda: <value>`
  - `Status: <value>`
- Actions:
  - `Kembali ke dashboard`
  - `Reset filter dashboard`

Interaction:

- `Kembali ke dashboard` navigates to `/dashboard` with original `period`, `supplier`, and `mode`.
- `Reset filter dashboard` removes dashboard-derived query params and resets derived local state.
- Buttons should use available icon patterns, preferably lucide icons if already available in the app.

Tone:

- Indonesian operational language.
- No instructional text blocks.
- No marketing copy.

## Empty And Sparse States

When a dashboard filter results in no visible rows, destination pages should show a clear Indonesian state near the data region:

- `Tidak ada data untuk filter dashboard ini.`
- Secondary detail can name the active period/supplier/status when useful.

When partial data exists:

- Keep existing tables/cards visible.
- Show counts and chips so the narrowed scope is clear.

## Page-Specific UI Contracts

### Smart Stock

- Date inputs should reflect `period` conversion.
- Supplier chip appears when `supplier` exists, even if supplier is not a native visible filter control.
- Empty state appears in the stock table/list area, not as a full-page replacement.

### PO Batubara

- Selected year/month should match `period`.
- Selected month section should open automatically.
- Supplier chip appears and the monthly payload uses it.

### COA Reconciliation

- Date/status controls should mirror query params.
- Supplier chip appears when supplied.
- KPI/list/trend areas should represent the same filter scope.

### Dispute Monitor

- Status filter should mirror `status` or `umpire_status` query params.
- Supplier/period chips appear when supplied.
- Summary cards and table should use the same filter scope.

### Laporan

- Existing report filters remain.
- Shared drilldown bar appears above report content when opened from dashboard.
- Reset removes dashboard query context while preserving the page route.

## Responsive Requirements

- The drilldown bar wraps cleanly on mobile.
- Chips must not overflow their container.
- Buttons may stack on narrow screens.
- No text overlap with dashboard/page controls.

## Accessibility Requirements

- Buttons must be keyboard-focusable.
- Reset/back buttons need clear accessible labels.
- Chips are visual status labels and should not be the only source of filter state; page controls should still reflect filter values where native controls exist.

