# Phase 07: Upgrade Backlog Foundation - Research

**Researched:** 2026-05-11
**Status:** Ready for planning

## Scope Summary

Phase 7 has two coupled goals:

- Continue modularizing `server.py` by extracting auth/users, dashboard/laporan, COA, and smart-stock/sumber-pemakaian into routers and moving inline Pydantic request/response models into `backend/models/`.
- Add date-range and categorical filters to the four main rekap list endpoints and expose minimal matching controls in rekap/Laporan UI.

## Current Backend Shape

- `pltu-tenayan-full-backup/backend/server.py` is still 4,584 lines and remains the production source of truth.
- `backend/models/__init__.py` already contains 301 lines of extracted Pydantic schemas, but `server.py` still defines inline models including `AIQueryRequest`, `AISettingsUpdate`, smart-stock/sumber-pemakaian entries, `SmartBlendingRequest`, `COASettingsUpdate`, `UmpireProposal`, `UmpireResultInput`, and `COAManualInput`.
- `backend/routers/auth.py`, `backend/routers/data.py`, and `backend/routers/ai.py` exist, but are not safe to mount as-is. `routers/ai.py` still imports `emergentintegrations` and uses `ai_conversations`, both superseded by Phase 6 and ADR-012.
- `backend/utils/database.py` and `backend/utils/auth.py` exist and may be useful, but must be reconciled against current `server.py` runtime globals before being treated as canonical.

## Extraction Risk

High-risk contracts to preserve:

- `/api/auth/login`, `/api/auth/register`, `/api/auth/me`, `/api/users`
- malformed `/api/auth/*` bodies return HTTP 400 via custom validation handler
- missing bearer token on `/api/auth/me` remains FastAPI HTTPBearer 403
- list endpoints preserve ADR-008 pagination envelope
- COA export/download endpoints preserve response type and filename behavior
- Phase 6 OpenRouter and AI chat behavior must not regress
- no legacy collection names: `smart_stock`, `sumber_pemakaian`, `settings`, `ai_conversations`

Recommended extraction order:

1. Auth/users first, because dependencies are shared by all routers and the test surface is focused.
2. COA/settings/export, because tests already cover list, KPI, trend, supplier consistency, dispute, manual input, upload/export.
3. Smart-stock/sumber-pemakaian, because Phase 5 canonical collection work and Phase 6 smart-blending depend on these names.
4. Dashboard/laporan last, because dashboard data quality has known product concerns and should be preserved before redesign.

## Filtering Research

Existing list endpoints already accept `search`, `page`, and `page_size`:

- `/api/vessels` sorts by `time_arrival`
- `/api/barges` sorts by `ta`
- `/api/trucking` sorts by `ta`
- `/api/biomassa` sorts by `periode`

Recommended new parameters:

- `date_from`
- `date_to`
- `supplier`

Query-building rule:

- Add date predicates to the collection's chosen date field.
- Add `suppliers` regex or exact match for `supplier`; exact match is simpler and safer if the frontend populates values from `/api/suppliers`.
- Preserve existing `$or` search logic by combining filters at top-level with `$and` only if needed. Mongo can combine top-level field filters with `$or` safely:
  - `{"suppliers": supplier, "time_arrival": {"$gte": date_from, "$lte": date_to}, "$or": [...]}`

Potential date issue:

- Date values are strings, not guaranteed typed `datetime`. ISO-like string ranges work if stored as `YYYY-MM-DD` or ISO timestamps. Planner/executor should inspect representative test/fixture data before finalizing the helper and add tests that pin the selected behavior.

## Frontend Research

The four rekap pages (`VesselPage.js`, `BargePage.js`, `TruckingPage.js`, `BiomassaPage.js`) currently:

- fetch `page=1&page_size=10000` from backend,
- apply client-side pagination with `ITEMS_PER_PAGE=100`,
- only react to `search`,
- reverse the result array locally.

`LaporanPage.js` already has:

- active tab selection,
- server pagination (`PAGE_SIZE=50`),
- supplier filter state and `/api/suppliers`,
- export buttons and current table summaries.

Recommended frontend plan:

- For the four rekap pages, keep existing local pagination for this phase but add server-side filters to the `page_size=10000` fetch.
- Add `dateFrom`, `dateTo`, and `supplier` state; include non-empty params in the axios request.
- Reset `currentPage` to `1` when any filter changes.
- Reuse current `Input`, `Select`, and `Button` components; avoid new design systems.
- For `LaporanPage`, add `dateFrom/dateTo` into `fetchData` params and filter controls near the existing search/supplier area.

## Tests To Add

Backend:

- Extend `test_pagination_shape.py` or create `test_rekap_filters.py` with seeded records for vessels, barges, trucking, biomassa.
- Assert `date_from/date_to` filters include in-range record and exclude out-of-range record.
- Assert `supplier` filter returns only matching supplier.
- Assert pagination envelope still matches ADR-008 when filters are present.

Refactor:

- Re-run existing auth, pagination, COA, dashboard, smart-blending, and AI chat tests after each extraction slice.
- Add grep gates:
  - no `emergentintegrations` imports in active backend code
  - no `ai_conversations` collection reads
  - extracted routes are mounted exactly once

Frontend:

- At minimum, `yarn build` must pass.
- If Playwright is available, smoke Laporan filter controls and one rekap page filter control visually. Otherwise rely on build plus backend tests.

## Planning Recommendation

Split Phase 7 into five plans:

1. Auth/users extraction and model cleanup.
2. COA/settings/export extraction.
3. Smart-stock/sumber-pemakaian extraction.
4. Rekap date/supplier filters in backend with tests.
5. Minimal filter UI in rekap/Laporan, plus dashboard redesign note/runway.

This order follows the user's refactor-first choice while keeping the frontend filter work late enough to depend on a stable backend contract.
