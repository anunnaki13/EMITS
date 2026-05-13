# Phase 07: Upgrade Backlog Foundation - UI Spec

**Generated:** 2026-05-11
**Status:** Ready for planning

## UI Scope

Phase 7 UI work is limited to minimal, consistent filtering controls for existing rekap and Laporan pages.

In scope:

- Add date range controls (`date_from`, `date_to`) to Vessel, Barge, Trucking, Biomassa, and Laporan views.
- Add one categorical supplier filter where supplier data is available.
- Preserve current page structure, tables, modals, upload actions, and pagination behavior.
- Keep controls compact and utilitarian.

Out of scope:

- Full dashboard redesign.
- New dashboard information architecture.
- Full filter-builder panel with many dimensions.
- Visual overhaul of table/card system.

## Required UX Behavior

- Filter controls sit near the existing search/filter controls, above the table.
- Changing search/date/supplier resets local page state to `1`.
- Empty filters are omitted from query params.
- A clear/reset button resets search, date range, supplier, and page.
- Loading state uses existing page loading patterns.
- No filter control should shift table layout during loading.

## Visual Contract

- Use existing Shadcn/Tailwind primitives already in the app:
  - `Input` for `type=date`
  - `Select` for supplier
  - `Button` for reset
  - existing icons from `lucide-react` where already imported (`Filter`, `Search`)
- Do not introduce large floating cards or nested cards for filters.
- On desktop, controls can sit in a responsive row.
- On mobile, controls wrap into a single-column or two-column compact layout without text overlap.

## Dashboard Direction For Future Phase

User explicitly wants dashboard UX redesigned because the current dashboard feels arbitrary. Future dashboard should prioritize:

- monitoring stock batubara,
- monitoring jadwal vs realisasi kedatangan bahan bakar,
- monitoring dispute/umpire batubara.

Phase 7 should not implement this redesign, but backend refactor should avoid making it harder.
