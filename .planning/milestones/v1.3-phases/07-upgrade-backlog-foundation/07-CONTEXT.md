# Phase 07: Upgrade Backlog Foundation - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 turns the stabilized EMITS codebase into an upgrade-ready foundation without changing the core product contract. The phase has two tracks:

1. Continue the `server.py` modular refactor by extracting the auth, dashboard/laporan, COA, and smart-stock surfaces into routers and moving remaining inline Pydantic schemas into `backend/models/`.
2. Add advanced filtering/date-range support to the four main rekap list surfaces (vessels, barges, trucking, biomassa), then expose a minimal, consistent date/category filter UI in the existing rekap and Laporan pages.

This phase is not a dashboard redesign phase. Dashboard UX was raised during discussion and is captured as a locked product direction for the next UI/dashboard phase: the dashboard should be reorganized around operational monitoring, especially stock batubara, jadwal vs realisasi kedatangan bahan bakar, and dispute/umpire monitoring. Phase 7 may preserve/refactor dashboard backend contracts, but should not attempt a full dashboard visual redesign unless the roadmap is explicitly updated.

</domain>

<decisions>
## Implementation Decisions

### Execution Strategy

- **D-01:** Start with refactor-first. Extract routers/models while preserving existing API behavior and keeping the Phase-4 test suite green, then add filtering. This is the selected option from user choice `1,1`.
- **D-02:** Avoid a broad "big bang" rewrite. Plans should be sequenced as small contract-preserving slices, with tests after each major extraction.
- **D-03:** Existing `backend/routers/auth.py`, `backend/routers/data.py`, and `backend/routers/ai.py` are not authoritative. They appear stale or incomplete: `routers/ai.py` still references `emergentintegrations` and `ai_conversations`, which Phase 6/ADR-012 superseded. Planner must either rewrite them from current `server.py` behavior or replace them; do not blindly mount stale routers.
- **D-04:** Keep auth dependencies (`get_current_user`, `require_role`, token helpers) importable from a stable place. If moved, all routers and tests must use one canonical source. The auth validation handler behavior for `/api/auth/*` returning 400 on malformed auth bodies must be preserved.

### Router Extraction Scope

- **D-05:** Extract these surfaces in Phase 7: auth/users, dashboard/laporan, COA reconciliation/settings/export, smart-stock/sumber-pemakaian. Rekap CRUD/upload surfaces (vessels, barges, trucking, biomassa) may remain in `server.py` unless needed for filter work, but shared filtering helpers may live outside `server.py`.
- **D-06:** Router extraction must preserve `/api/*` paths exactly. Frontend `REACT_APP_BACKEND_URL` and route call sites should not need path migrations.
- **D-07:** `server.py` should become smaller and primarily compose `FastAPI`, middleware, exception handlers, app startup globals, and router includes. It does not need to become tiny in one phase; "meaningfully smaller" is sufficient if the required surfaces are extracted and tests pass.

### Models

- **D-08:** Pydantic models should live under `backend/models/`. The current `backend/models/__init__.py` already contains many schemas, but `server.py` still has inline classes such as AI/settings/smart-stock/COA request models. Phase 7 should move the inline models used by extracted routers into model modules or a cleaned `models/__init__.py`.
- **D-09:** Do not change public response fields while moving models. Model extraction is mechanical unless tests expose a current contract mismatch.

### Filtering Contract

- **D-10:** Add `date_from` and `date_to` query parameters to vessels, barges, trucking, and biomassa list endpoints.
- **D-11:** Add at least one categorical filter beyond `search` for each of the four list endpoints. Recommended baseline: `supplier` for all four; optional mode-specific filters can be added only if cheap and covered by tests.
- **D-12:** Preserve the pagination envelope exactly: `{items,total,page,page_size,total_pages}`. Filtering must apply to both `count_documents` and the paginated `find`.
- **D-13:** Date filtering should target the operational arrival/receipt date field per collection:
  - vessels: `time_arrival`
  - barges: `ta`
  - trucking: `ta`
  - biomassa: `periode` unless research shows a better receipt-date field in production data.
- **D-14:** Date strings in the DB appear to be string fields. Planner/researcher must inspect representative live/test documents and existing tests before choosing exact Mongo range predicates. Prefer a helper that handles ISO-like/string dates consistently and does not break current data.

### Filter UI

- **D-15:** User selected minimal, consistent filter UI. Add date range controls and one categorical filter to existing rekap/Laporan surfaces using current components and page layout. Do not create a full filter-builder redesign in Phase 7.
- **D-16:** Use existing UI primitives (`Input`, `Select`, `Button`, current page header/table/pagination patterns). Keep controls compact and utilitarian, not a dashboard-style card redesign.
- **D-17:** Filter state must round-trip to backend query params and reset page to 1 when filters change. Pagination should continue to work.

### Dashboard Product Direction

- **D-18:** Dashboard redesign is a user-requested product direction, but not Phase 7 execution scope unless roadmap is changed. The future dashboard should be organized around:
  - monitoring stock batubara,
  - monitoring jadwal vs realisasi kedatangan bahan bakar,
  - monitoring dispute/umpire batubara.
- **D-19:** Phase 7 dashboard/laporan backend refactor should avoid making the dashboard harder to redesign later. If a dashboard router is extracted, keep functions/data shapes understandable and document any existing placeholder or "asal-asalan" data sources found during extraction.

### the agent's Discretion

- Exact module/file names under `backend/routers/` and `backend/models/`, as long as imports remain clear and tests pass.
- Whether to extract helper utilities for pagination/date filters into `backend/utils/` or keep them local to router modules.
- Whether to split filter UI into reusable components now or keep it page-local. Prefer reuse only if it avoids real duplication across the four rekap pages.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope

- `.planning/ROADMAP.md` §"Phase 7: Upgrade Backlog Foundation" — goal, dependencies, success criteria.
- `.planning/REQUIREMENTS.md` §"Upgrade Backlog Foundation (UPGRADE)" — UPGRADE-01..05.
- `.planning/PROJECT.md` §"Active" — DEBT-02 and FEAT-01 active scope.

### Locked Architecture and Contracts

- `.planning/decisions/ADR-001-mongodb-datastore.md` — MongoDB remains datastore.
- `.planning/decisions/ADR-002-fastapi-python-backend.md` — FastAPI/Python backend stack.
- `.planning/decisions/ADR-003-react-frontend-stack.md` — React/Tailwind/Shadcn frontend stack.
- `.planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md` — JWT/bcrypt/role auth contract.
- `.planning/decisions/ADR-006-api-prefix-and-frontend-base-url.md` — `/api/*` prefix and frontend base URL.
- `.planning/decisions/ADR-007-persistence-projection-uuid-iso.md` — `_id` projection, UUID `id`, ISO datetime expectations.
- `.planning/decisions/ADR-008-pagination-shape.md` — pagination envelope must not change.
- `.planning/decisions/ADR-009-canonical-smartstock.md` — smartstock canonical collection.
- `.planning/decisions/ADR-010-canonical-sumberpemakaian.md` — sumberpemakaian canonical collection.
- `.planning/decisions/ADR-011-canonical-app-settings.md` — app_settings canonical collection.
- `.planning/decisions/ADR-012-canonical-ai-chat-history.md` — avoid reintroducing `ai_conversations`.

### Prior Phase Evidence

- `.planning/phases/04-test-suite-stabilization/VERIFICATION.md` — Phase-4 test suite baseline and risk areas.
- `.planning/phases/05-collection-naming-debt-resolution/05-VERIFICATION.md` — canonical collection cleanup.
- `.planning/phases/06-operational-unblocks/06-06-SUMMARY.md` — Phase-6 OpenRouter/AI chat final state and `server.py` compatibility alias.

### Code Targets

- `pltu-tenayan-full-backup/backend/server.py` — current monolith; route and inline model source of truth.
- `pltu-tenayan-full-backup/backend/models/__init__.py` — existing extracted models; use as baseline but clean as needed.
- `pltu-tenayan-full-backup/backend/routers/auth.py` — existing router candidate; must be reconciled against current `server.py`.
- `pltu-tenayan-full-backup/backend/routers/data.py` — existing rekap router candidate; may be stale but useful for helper patterns.
- `pltu-tenayan-full-backup/backend/routers/ai.py` — stale example; do not mount without removing `emergentintegrations` and `ai_conversations`.
- `pltu-tenayan-full-backup/backend/utils/auth.py` and `pltu-tenayan-full-backup/backend/utils/database.py` — existing shared utility candidates.
- `pltu-tenayan-full-backup/backend/tests/` — contract preservation gate. Relevant files include `test_auth_session.py`, `test_auth_roles.py`, `test_pagination_shape.py`, `test_upload_excel.py`, `test_coa_reconciliation.py`, `test_dashboard_advanced.py`, `test_smart_blending_data.py`.

### Frontend Targets

- `pltu-tenayan-full-backup/frontend/src/pages/VesselPage.js`
- `pltu-tenayan-full-backup/frontend/src/pages/BargePage.js`
- `pltu-tenayan-full-backup/frontend/src/pages/TruckingPage.js`
- `pltu-tenayan-full-backup/frontend/src/pages/BiomassaPage.js`
- `pltu-tenayan-full-backup/frontend/src/pages/LaporanPage.js`
- `pltu-tenayan-full-backup/frontend/src/components/Pagination.js`
- `pltu-tenayan-full-backup/frontend/src/components/ui/input.jsx`
- `pltu-tenayan-full-backup/frontend/src/components/ui/select.jsx`
- `pltu-tenayan-full-backup/frontend/src/components/ui/button.jsx`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `backend/models/__init__.py` already holds many Pydantic schemas for auth, rekap, PO, merit order, smart stock, AI, and COA. Phase 7 should build on this rather than inventing a second model package.
- `backend/routers/auth.py` already contains a router-shaped auth extraction and notes the auth validation handler requirement. It may be reusable after confirming parity with `server.py`.
- `backend/routers/data.py` contains a router-shaped version of vessels/barges/trucking/biomassa CRUD and a `paginate_query` helper. Treat it as a reference, not source of truth.
- `frontend/src/components/Pagination.js` and existing page-level search/pagination patterns are the baseline for filter UI.

### Established Patterns

- Backend uses FastAPI `APIRouter`, Motor async Mongo calls, projection `{"_id": 0}`, and role dependencies.
- List endpoints currently support `search`, `page`, and `page_size`; Phase 7 extends that contract without changing response shape.
- Frontend pages use Axios against `REACT_APP_BACKEND_URL`, local state for search/page/page_size, and Shadcn/Tailwind controls.
- Tests use a spawned test backend and production-shaped fixtures; Phase 7 should prove refactor by running existing tests unchanged where possible.

### Integration Points

- Router include must happen in `server.py` after app/router creation and before `app.include_router(api_router)`, or via preserving the existing `api_router` structure. Planner must inspect current app composition before changing includes.
- Auth dependency imports are high-risk because many routes depend on `get_current_user` and `require_role`.
- Filtering touches both backend list endpoints and frontend page query construction; every filter change needs pagination reset and test coverage.
- Dashboard backend extraction touches operational data that user considers currently low quality. Preserve current behavior in Phase 7 while documenting improvement targets for dashboard redesign.

</code_context>

<specifics>
## Specific Ideas

- User selected refactor-first and minimal consistent filter UI.
- User explicitly wants dashboard UX improved later because the current dashboard appears arbitrary. Future dashboard should prioritize stock batubara, jadwal vs realisasi kedatangan bahan bakar, and dispute/umpire batubara monitoring.
- For this phase, avoid a wide UI redesign. Keep the UI work focused on date-range and categorical filters in rekap/Laporan pages so the backend refactor remains controllable.

</specifics>

<deferred>
## Deferred Ideas

### Dashboard redesign

- **Origin:** User feedback during Phase 7 context gathering.
- **Desired direction:** Rebuild dashboard around operational monitoring: stock batubara, jadwal vs realisasi kedatangan bahan bakar, dispute/umpire batubara.
- **Why deferred:** Phase 7 is already scoped to backend modularization plus filter/date-range work. Full dashboard UX redesign belongs in Phase 8 or a dedicated dashboard phase.

### Full filter panel / advanced filter builder

- **Origin:** Phase 7 filter UI choice.
- **Why deferred:** User selected minimal consistent filter UI for this phase. Rich panel with supplier/mode/status/reset across all pages can follow once backend contract is stable.

</deferred>

---

*Phase: 07-upgrade-backlog-foundation*
*Context gathered: 2026-05-11*
