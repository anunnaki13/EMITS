# Phase 8 UI Spec — Operational Dashboard & Polish

Created: 2026-05-11

## Dashboard Information Architecture

The first viewport should answer three operational questions:

1. **How much coal stock is available?**
   - Current stock estimate.
   - Latest stock date.
   - Average daily burn.
   - Days of supply.

2. **Are scheduled fuel arrivals matching reality?**
   - Upcoming / scheduled PO arrivals.
   - Realized arrivals by mode.
   - Schedule-vs-realization gap.

3. **Are there active coal quality disputes?**
   - Critical/warning COA counts.
   - Umpire proposed / in progress / completed.
   - Highest-risk recent dispute rows.

## Layout Rules

- Keep the dashboard dense and operational, not marketing-like.
- Use compact KPI tiles, tables, and charts that support scanning.
- Avoid decorative sections and nested cards.
- Period filter must be visible near the title and should apply to dashboard data.
- Primary dashboard modules:
  - Stock Batubara.
  - Jadwal vs Realisasi Kedatangan BB.
  - Dispute / Umpire Batubara.
  - Supporting trend / composition charts only after the operational modules.

## Copy Rules

- Use Indonesian operational labels.
- Avoid explanatory prose inside the app.
- Use concise labels such as `Stok Saat Ini`, `Hari Supply`, `Jadwal`, `Realisasi`, `Umpire Proses`.

## Verification

- Frontend build must pass.
- Dashboard backend tests must verify response shape.
- Runtime smoke should confirm the dashboard endpoint returns HTTP 200.
