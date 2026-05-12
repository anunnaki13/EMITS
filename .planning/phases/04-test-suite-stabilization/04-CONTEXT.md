# Phase 04: Test Suite Stabilization - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

A single command — `pytest backend/tests -q` — exits 0 on a clean checkout against an isolated test database, with explicit coverage for: auth (login/role/expired/me), pagination contract on the seven list endpoints, Excel upload (one fixture-driven test per receipt mode), COA reconciliation (KPI + trend + supplier-consistency + export), AI endpoints (mocked, no LLM budget), and dashboard (`/stats`, `/advanced`). Output: TEST-01..07 closed, conftest extended to spawn the backend automatically, an `AIClient` Protocol introduced as a stub seam, and four sanitized synthetic Excel fixtures committed to the repo.

**In scope:** TEST-01..07 (REQUIREMENTS.md lines 35-41); conftest extension (auto-spawn uvicorn subprocess); `AIClient` Protocol introduction + production wrap of existing `EmergentLLMClient` behind it (zero behavior change); FakeAIClient stub for tests; isolated `pltu_tenayan_test_*` database lifecycle (seed → run → teardown); four sanitized synthetic xlsx fixtures (vessel/barge/trucking/biomassa); test coverage gaps for vessels/barges/trucking/biomassa pagination + Excel upload + AI endpoints + dashboard happy-path.

**Out of scope:**
- LLM provider migration (Gemini → OpenRouter) and `EmergentLLMClient` rename — captured as deferred idea, owned by a future dedicated phase (propose insert via `/gsd-phase` after Phase 4; candidate position: between Phase 4 and Phase 5, or fold into Phase 6 Operational Unblocks).
- Refactoring existing 7 test files (1634 lines) from `requests`-against-HTTP to `TestClient` in-process — explicitly rejected during discussion (preserve Phase-2 conftest pattern; auto-spawn subprocess closes TEST-01 without rewriting working tests).
- Real-Excel-sample parser verification — owned by Phase 6 OPS-02 (synthetic fixtures here only validate that parser paths execute end-to-end against committed `.xlsx` files; they do not assert numerical correctness against production samples).
- CI / GitHub Actions setup — Phase 4 boundary is "single local command exits 0"; remote CI is a later concern.
- Coverage threshold enforcement (e.g., `pytest --cov-fail-under`) — happy-path coverage for the seven SC sections is required; numerical coverage gating is deferred.
- Frontend test surface (Jest, React Testing Library) — Phase 4 is backend-only.

</domain>

<decisions>
## Implementation Decisions

### Test database lifecycle
- **D-01:** All Phase 4 tests run against a per-session isolated MongoDB database named `pltu_tenayan_test_<sessionid>`. The conftest session-scoped fixture creates the DB at session start, seeds it with the minimum data each test class needs (factory functions, not fixture dumps), and drops it at session teardown. The live `pltu_tenayan` database is **never** touched by tests under any code path. This carries forward and propagates the pattern Phase-2 plan 02-02 introduced for auth tests.
- **D-02:** Seed data uses small Python factory helpers in `tests/factories/` (vessel, barge, trucking, biomassa, po_batubara, merit_order, coa, user) rather than committed JSON dumps. Factories are deterministic via fixed seeds when needed for snapshot assertions.
- **D-03:** The session-scoped fixture passes the test DB name to the running backend via a `MONGO_TEST_DB_NAME` env var that the backend's startup config reads when present (overriding `DB_NAME`). The backend already reads `DB_NAME` from env per Phase-3 plan 03-05 reconciliation; the override is additive, not a refactor.

### AI mock seam
- **D-04:** Phase 4 introduces an `AIClient` Protocol (or ABC) in the backend (e.g., `app/ai/client.py`). The existing `EmergentLLMClient` is wrapped behind this interface — **no rename, no rewrite**. Production code paths inject the `AIClient`-typed dependency; concrete provider stays `EmergentLLMClient` for now.
- **D-05:** Tests stub the interface via a `FakeAIClient` defined in `tests/fakes/ai_client.py`. The fake returns canned response shapes per AI module (general, blending, boiler, contract, logistics, smart-stock, COA). No external HTTP, no LLM budget consumed.
- **D-06:** Production wiring uses FastAPI dependency injection (`Depends(get_ai_client)` returning the concrete `EmergentLLMClient`). The conftest spawns the test backend subprocess with `AI_FAKE=1` in its environment; `get_ai_client()` reads that env var at the FastAPI app boundary and returns `FakeAIClient` when set. **Amended 2026-05-11:** the original wording said "the conftest overrides `get_ai_client`" using `app.dependency_overrides`. Phase 4 RESEARCH §Focus 1 proved `app.dependency_overrides` does NOT cross the subprocess boundary that D-11/D-12 mandate; the env-var seam is the correct structural answer. The seam is identical for production migration purposes (the future OpenRouter phase swaps the implementation `get_ai_client()` returns when `AI_FAKE` is unset).
- **D-07:** Provider migration (Gemini → OpenRouter) is intentionally NOT done in Phase 4. The interface seam is precisely so that the migration phase can swap implementations without touching tests. This is the `IMPLICIT-005` boundary Phase 4 must respect.

### Excel fixture provenance
- **D-08:** Four sanitized synthetic xlsx fixtures live at `pltu-tenayan-full-backup/backend/tests/fixtures/excel/`:
  - `vessel_minimal.xlsx`
  - `barge_minimal.xlsx`
  - `trucking_minimal.xlsx`
  - `biomassa_minimal.xlsx`
  Each has 5–10 dummy rows, headers identical to the production format (so the parser's column-mapping path is exercised), no real PT names / contract numbers. Total fixture size <50 KB.
- **D-09:** The parser path validation in TEST-04 asserts that each upload endpoint returns success (status 200/201, the expected response shape) **and** that a small, deterministic field on at least one row round-trips into the expected MongoDB collection. It does NOT assert against production sample numerical totals — that is Phase 6 OPS-02's job using the real `total penerimaan.xlsx`.
- **D-10:** Header-variant edge cases (slightly different column ordering / casing seen in production samples) are NOT covered by the minimal fixtures; they are deferred to Phase 6 OPS-02 alongside the real-sample verification. Phase 4 adds a `tests/fixtures/excel/HEADER_VARIANTS.md` note pointing forward to Phase 6 so the gap is traceable.

### Test runner posture
- **D-11:** `pytest backend/tests -q` is the canonical command. The conftest defines a session-scoped autouse fixture `_backend_lifecycle` that:
  1. Probes `http://localhost:8013/api/health`. If 200, reuses the running backend.
  2. If connection-refused, spawns `uvicorn server:app --host 127.0.0.1 --port 8013` as a subprocess (using the project `.venv/bin/uvicorn`), exports `MONGO_TEST_DB_NAME=pltu_tenayan_test_<sessionid>`, polls health for up to 30 s, fails the session if not ready.
  3. Records the spawned PID to `tests/.backend.pid` so a subsequent crashed run can clean up.
  4. At session teardown, kills the spawned PID (only if Phase-4 spawned it, not if it pre-existed) and drops the test DB.
- **D-12:** Existing 7 test files (1634 lines) are NOT refactored to `TestClient`. Conftest spawn-or-reuse logic preserves the existing `requests`-based pattern; new tests written in Phase 4 (vessels/barges/trucking/biomassa pagination, excel upload per mode, AI mocked, dashboard) follow the same pattern for consistency.
- **D-13:** Destructive tests remain gated by `RUN_DESTRUCTIVE_TESTS=1` env var per Phase-2 plan 02-03. Phase 4 does not change this default; the gate continues to skip-by-default.

### Claude's Discretion
- Exact `pytest.ini` / `pyproject.toml` placement (under `pltu-tenayan-full-backup/` root or under `backend/`), conftest naming convention, and factory-function signatures — planner picks based on existing project layout.
- Whether `tests/factories/` and `tests/fakes/` are flat modules or sub-packages — planner decides at planning time.
- Specific assertion helpers for the pagination contract (`assert_pagination_shape(resp_json)` etc.) — planner factors out as needed.
- Exact mechanism for the `MONGO_TEST_DB_NAME` env-var override in `server.py` (read at startup vs. read per-request) — planner picks the smallest-blast-radius patch.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase boundary + requirements
- `.planning/ROADMAP.md` §"Phase 4: Test Suite Stabilization" — goal + 7 success criteria + dependencies (Phase 2, Phase 3) + requirement IDs (TEST-01..07).
- `.planning/REQUIREMENTS.md` lines 35-41 — TEST-01..07 verbatim text.
- `.planning/PROJECT.md` §"Active" item STAB-05 — backend test suite green end-to-end (auth, pagination, Excel upload, COA KPI/export, AI endpoints mocked, dashboard advanced).

### Architectural anchors (locked ADRs from Phase 3)
- `.planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md` — auth contract test patterns (login success/failure/role-denied/token-expired all derive from here).
- `.planning/decisions/ADR-008-pagination-shape.md` — `{items, total, page, page_size, total_pages}` shape that TEST-03 asserts on each list endpoint.
- `.planning/intel/constraints.md` — CONS-pagination-shape, CONS-auth-header (error-code semantics tested in TEST-02).

### Phase-2 carry-forward (test pattern source-of-truth)
- `pltu-tenayan-full-backup/backend/tests/conftest.py` — existing 93-line conftest with `_require_env` + admin/operator/viewer fixtures + BASE_URL pattern. Phase 4 EXTENDS this file; does NOT replace it.
- `pltu-tenayan-full-backup/backend/tests/test_auth_session.py` — session-rehydrate test pattern (TEST-02 builds on this).
- `pltu-tenayan-full-backup/backend/tests/test_auth_roles.py` — admin/operator/viewer role-tier test pattern (TEST-02 destructive-gate continues this).
- `pltu-tenayan-full-backup/docs/audit/AUTH_CONTRACT.md` — auth contract definitions (TEST-02 source-of-truth).
- `pltu-tenayan-full-backup/docs/audit/CREDENTIAL_HYGIENE.md` — env-var contract (`TEST_ADMIN_PASSWORD` etc.). Phase 4 MUST NOT inline credentials in any new test file.
- `pltu-tenayan-full-backup/memory/test_credentials.md` — gitignored env-var source. Operator runbook references this.

### Phase-3 carry-forward (regenerated docs that test setup cites)
- `pltu-tenayan-full-backup/API_REFERENCE.md` — regenerated from `/openapi.json` (Plan 03-03). Pagination Contract + Auth Contract + Error Code Map sections are the spec-truth for what TEST-02 / TEST-03 / TEST-05 / TEST-07 assert against.
- `pltu-tenayan-full-backup/docs/audit/API_REFERENCE_SPOTCHECK.md` — Plan 03-03 spot-check log; TEST-04 / TEST-06 will close out endpoints currently marked `verified: schema-only`.
- `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` — Plan 03-05 audit identifies which collection name is the active read target per duplicate pair. Phase 4 tests MUST read/write canonical names only.
- `pltu-tenayan-full-backup/LOCAL_SETUP.md` §"VPS Service Recovery (post-restart)" — operator-restart runbook. Phase 4 conftest auto-spawn uses the same uvicorn invocation pattern (`source .venv/bin/activate; uvicorn server:app --port 8013`).
- `pltu-tenayan-full-backup/documentation.md` §"Known Issues" — Plan 03-04. Phase 4 tests do NOT need to gate on Smart Blending budget (mocked); but TEST-06 entries reference this section so the reader knows why the AI tests are mock-only.

### Backend code anchors (read for shape, not modification scope)
- `pltu-tenayan-full-backup/backend/server.py` — main FastAPI app. Phase 4 reads endpoint signatures, request models, dependency wiring. Modification is limited to the `AIClient` injection seam (D-04, D-06) and the `MONGO_TEST_DB_NAME` env-var read (D-03).
- `pltu-tenayan-full-backup/backend/.env` — env-var contract (`MONGO_URL`, `DB_NAME`, `JWT_SECRET`, `CORS_ORIGINS`, `EMERGENT_LLM_KEY`). Phase 4 adds `MONGO_TEST_DB_NAME` as an optional override.
- `pltu-tenayan-full-backup/backend/requirements.txt` — pytest 9.0.2 + requests 2.32.5 already present; no new test deps unless `pytest-asyncio` is needed for any async fixture (planner decides).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`tests/conftest.py` `_require_env` + admin/operator/viewer fixtures** (93 lines): Phase 4 extends this file with new session-scoped fixtures (`_backend_lifecycle`, `_test_db_lifecycle`, `_ai_client_override`). Existing fixtures are preserved verbatim.
- **Phase-2 test pattern (`requests.Session` + BASE_URL + env-var creds)**: 7 test files (1634 lines) follow this. New Phase-4 test files mirror the same shape — no migration to TestClient.
- **`pltu-tenayan-full-backup/Loading.xlsx` / `Unloading.xlsx` / `Lab_Internal.xlsx`** (referenced for header layout only): Phase 4 mirrors header structure in synthetic fixtures but does NOT commit these files into `tests/fixtures/`. They stay in the repo root for Phase 6 OPS-02.

### Established Patterns
- **Env-var driven creds** — every credential in tests is sourced from `os.environ` via `_require_env`. Inline literals are forbidden by `docs/audit/CREDENTIAL_HYGIENE.md` and the credential scanner enforces it.
- **Destructive opt-in** — `RUN_DESTRUCTIVE_TESTS=1` gate from Phase-2 plan 02-03. Phase 4 honors and extends to any new write/delete-heavy tests.
- **Session-scoped fixtures** — Phase-2 plan 02-02 introduced session-scoped login. Phase 4 adds session-scoped backend lifecycle and DB lifecycle on the same scope tier.
- **Pagination shape contract** — `{items, total, page, page_size, total_pages}` (ADR-008). Phase 4 will likely add a shared `assert_pagination_shape(resp)` helper to keep TEST-03 assertions DRY.
- **Two-repo commit boundary** — backend tests and fixtures commit to `pltu-tenayan-full-backup/` (the live-app inner repo); SUMMARY.md / CONTEXT.md / STATE.md / ROADMAP.md commit to the outer planning repo. This is the same protocol Phases 1-3 used.

### Integration Points
- **`server.py` startup config**: Phase 4 adds an env-var read (`MONGO_TEST_DB_NAME`) that overrides `DB_NAME` when set. Smallest possible patch — read at startup, no per-request branching.
- **AI client construction site in `server.py`**: currently `EmergentLLMClient(...)` is instantiated and used directly. Phase 4 wraps the construction in a FastAPI `Depends(get_ai_client)` provider. All AI endpoints accept the dependency-injected client. Tests override the provider.
- **Backend lifecycle fixture vs LOCAL_SETUP runbook**: the auto-spawn subprocess invocation MUST match the runbook's uvicorn command (`source .venv/bin/activate` + `uvicorn server:app --host 0.0.0.0 --port 8013`). Drift between the two is a documentation bug — keep them in sync.

</code_context>

<specifics>
## Specific Ideas

- The user explicitly raised provider migration (Gemini → OpenRouter) during AI-mock discussion. The provider-agnostic interface (D-04) is the structural answer that lets Phase 4 finish without prejudicing the future migration. The user agreed.
- "ubah namanya, buatkan atau desainkan yang terbaru" — the user asked for `EmergentLLMClient` to be renamed and redesigned. This is captured in `<deferred>` as a future-phase task; Phase 4 does not act on it.

</specifics>

<deferred>
## Deferred Ideas

### LLM provider migration to OpenRouter
- **Origin:** User raised during Phase-4 AI-mock discussion (2026-05-11): "saya menggunakan openrouter bukan gemini seperti yang sekarang".
- **Why deferred:** PROJECT.md "Out of Scope" line 87 (IMPLICIT-005) and ROADMAP Phase 6 boundary. Switching providers + renaming `EmergentLLMClient` is a new capability, not implementation clarification.
- **Proposed home:** A new dedicated phase (candidate label: "AI Provider Migration"), inserted via `/gsd-phase` after Phase 4 and before / merged with Phase 6 Operational Unblocks. The phase would:
  1. Replace `emergentintegrations` with the OpenRouter Python client (or `httpx` direct).
  2. Rename `EmergentLLMClient` to a provider-agnostic name (e.g., `OpenRouterClient`, or rename the wrapper to `LLMClient` keeping `AIClient` as the Protocol).
  3. Update `EMERGENT_LLM_KEY` env var to `OPENROUTER_API_KEY`.
  4. Re-run Phase-4 AI tests against the new implementation through the same `AIClient` interface — no test changes expected.
- **Phase 4 enabler:** D-04..D-07 (the `AIClient` Protocol + dependency injection) is precisely the seam this future phase plugs into. Phase 4 makes the migration plug-and-play.

### Excel header-variant edge cases (Phase 6 OPS-02)
- Header ordering / casing variants observed in production samples are NOT covered by Phase-4 minimal fixtures. Tracked via `tests/fixtures/excel/HEADER_VARIANTS.md` pointer.

### Numerical coverage gating (`pytest --cov-fail-under`)
- Phase 4 closes happy-path coverage for the seven SC sections. Numerical coverage thresholds are not enforced; can be added in a polish phase if desired.

### Frontend test surface (Jest / RTL)
- Frontend tests are NOT in Phase 4 scope. Tracked as a future phase (UI Polish or dedicated frontend testing phase) — not yet scheduled.

### CI / GitHub Actions
- Local `pytest backend/tests -q` exit 0 is the SC bar. Wiring this to a hosted CI runner is post-milestone-v1.0.

### Reviewed Todos (not folded)
- None — `gsd-sdk query todo.match-phase 4` returned 0 todos.

</deferred>

---

*Phase: 04-test-suite-stabilization*
*Context gathered: 2026-05-11*
