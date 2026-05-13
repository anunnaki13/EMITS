# Phase 06: Operational Unblocks - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Resolve four operational blockers that have been carried forward since project ingest: (a) the Smart Blending AI is non-functional because the `EMERGENT_LLM_KEY` (Gemini-via-emergentintegrations) budget is exhausted AND a latent data-path bug surfaced by Phase 5 leaves smart-stock aggregation returning zeros; (b) the smart-blending UX surfaces raw `BadGatewayError` to the user when the LLM call fails; (c) the Excel parser has never been verified against a real-shape sample; (d) the AI chat UI does not surface persisted conversation history. Phase 6 closes all four via OpenRouter migration (using the `AIClient` Protocol seam built in Phase 4), a smart-blending-related data-correctness audit, a parser regression-fixture pass against the three real production xlsx files already in the repo, and a sidebar+main AI chat UI that shows cross-session history from the canonical `ai_chat_history` collection (ADR-012).

**In scope:**
- OPS-01: Provider migration (Gemini-via-emergentintegrations → OpenRouter) + smart-blending data-correctness audit (smart-stock summary, sumberpemakaian aggregations, blending suggestion endpoint) + 3 successful Smart Blending recommendations against live data on target-GCV parameter sets 4000 / 4200 / 4500.
- OPS-02: Retry-with-backoff in the smart-blending request path + user-facing Indonesian-localized error toast with retry button + clear error message when budget exhausted (no raw `BadGatewayError` / `BudgetExceededError` surfaced).
- OPS-03: Excel parser verification using the three real production xlsx samples already in the repo (`pltu-tenayan-full-backup/Loading.xlsx`, `Unloading.xlsx`, `Lab_Internal.xlsx`) as proxies for the missing `total penerimaan.xlsx` (which the operator has not yet provided; deferred to Phase 7 polish). Discrepancies fixed in the parser code; a sanitized regression-fixture subset (~50 rows per mode) committed.
- OPS-04: Frontend AI chat UI with sidebar (list of user's prior conversations, recent-first, auto-generated titles from first user message) + main panel (messages in the selected conversation) + lazy-load older messages on scroll + "New conversation" button. Reads from the canonical `ai_chat_history` collection (ADR-012) — NOT `ai_conversations` (the ROADMAP §"Phase 6" SC-4 wording is stale per Phase 5 lock-in and is reconciled at planning time).

**Out of scope:**
- The literal `total penerimaan.xlsx` parser verification — deferred to Phase 7 polish until the operator provides the file. Phase 6 closes OPS-03 against the three existing real xlsx samples as proxies.
- Multi-provider hybrid routing (try OpenRouter first, fall back to another LLM provider) — deferred to a future polish phase. Phase 6 commits to OpenRouter single-provider for this milestone.
- Cost-aware model routing (pick cheap model first, premium fallback) — deferred. Phase 6 picks one default model at planning time.
- Conversation export / search across history — deferred to Phase 8 polish.
- Re-implementation of the AI chat UI design system — extend the existing chat component pattern; minimum disruption.
- Replacement of the existing visualization / dashboard components — Phase 6 is AI-area-focused.
- Index rationalization on `ai_chat_history` collection — deferred to a polish phase if the post-migration UI surfaces a query that needs it.

</domain>

<decisions>
## Implementation Decisions

### LLM provider migration to OpenRouter (D-01..D-05 — closes OPS-01 provider side)

- **D-01:** **OpenRouter is the new LLM provider.** All Smart Blending + AI-query endpoints route through OpenRouter via the `AIClient` Protocol seam that Phase 4 introduced. The choice is locked: no hybrid, no fallback chain — single-provider for milestone v1.0. Future polish phase may revisit if cost / availability becomes an operator concern.

- **D-02:** **Rename `EmergentLLMClient` → `OpenRouterClient` + `emergent_wrapper.py` → `openrouter_client.py`.** The class implements the `AIClient` Protocol that Phase 4 introduced (`app/ai/client.py`). The new `OpenRouterClient` constructor reads `OPENROUTER_API_KEY` from env, hits the OpenRouter HTTPS API directly via `httpx` (no `emergentintegrations` dependency). `get_ai_client()` factory in `app/ai/client.py` continues to branch on `AI_FAKE=1` to return `FakeAIClient` for tests; otherwise returns the new `OpenRouterClient`.

- **D-03:** **Env-var rename:** `EMERGENT_LLM_KEY` → `OPENROUTER_API_KEY` across `backend/.env`, `backend/.env.example`, MIGRATION_RUNBOOK.md, LOCAL_SETUP.md (any references), CREDENTIAL_HYGIENE.md. The `OPENROUTER_API_KEY` is sourced from the operator's OpenRouter account (operator action — see runbook).

- **D-04:** **Default model = `openai/gpt-4o-mini`** (user-selected 2026-05-11). Pricing: ~$0.15 / $0.60 per 1M input/output tokens via OpenRouter. JSON mode (`response_format: {"type": "json_object"}`) is mature on this model. Handles Indonesian language prompts reliably. Cost characteristics: smart-blending recommendation prompts are ~2k input + ~1k output → ~$0.0009 per call (sub-rupiah). AI chat messages similar. The model identifier is configurable via env var `OPENROUTER_DEFAULT_MODEL` (default `openai/gpt-4o-mini`) so future operator changes don't require a code deploy. Decision rationale (per user feedback): OpenRouter migration was chosen for model variety + cost flexibility; defaulting to a premium model (e.g., Claude Sonnet at $3/$15) would defeat that purpose. If `gpt-4o-mini` response quality becomes inadequate, operator swaps the env var to a higher-tier model without touching code.

- **D-05:** **`emergentintegrations` dependency** is REMOVED from `requirements.txt` once `OpenRouterClient` lands. `httpx` is the only new outbound HTTP dependency; it's already in the FastAPI / Starlette dependency tree, so the requirements diff is `-emergentintegrations` and no addition.

### Smart-blending data-correctness audit (D-06..D-08 — closes OPS-01 data side)

- **D-06:** **Bundle data audit into OPS-01.** Phase 5 CP2 surfaced that `/api/ai/quick/smart-stock` returns zero values (aggregation fields don't match smartstock doc schema). The planner re-greps all `db.smartstock.aggregate(...)`, `db.sumberpemakaian.aggregate(...)`, and `db.smart-blending`-related aggregations in `server.py` and validates each `$sum` / `$avg` field name against the actual document schema by probing live data via `mongosh pltu_tenayan --eval "db.<col>.findOne()"` (read-only).

- **D-07:** **Fix mode:** for each mismatch found, fix the aggregation in `server.py` to use the correct field name. Add a unit test per fixed aggregation in `pltu-tenayan-full-backup/backend/tests/test_smart_blending_data.py` that asserts the endpoint returns a non-empty payload against a seeded test DB. Use the Phase-4 factories (`tests/factories/smartstock.py`, `sumberpemakaian.py`) to seed deterministic data; the test passes when the aggregation returns the expected non-zero numbers.

- **D-08:** **Validation gate:** OPS-01 SC-1 ("Smart Blending AI returns a successful recommendation against live data on at least three different parameter sets — target GCV 4000 / 4200 / 4500") is run as a manual smoke-test by the operator at cutover (`curl /api/smart-blending/recommend` with three different GCV bodies, response is `json.loads`-parseable per CONS-blending-ai-output, recommendation contains a non-empty blend list). Documented in the Phase-6 cutover runbook.

### User-facing error UX (D-09..D-10 — closes OPS-02)

- **D-09:** **Retry-with-backoff** in the smart-blending request path: `OpenRouterClient` wraps its outbound HTTP call in a 3-retry-with-exponential-backoff (1 s → 2 s → 4 s) for transient 5xx + 429 (rate limit). After exhaustion, raises a typed `LLMUnavailableError` (NOT a raw `httpx.HTTPStatusError`). The endpoint catches `LLMUnavailableError` and returns HTTP 503 with body `{"detail": "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar."}`.

- **D-10:** **Frontend error toast** in the AI chat + smart-blending UI: when the API returns 503 with the `LLMUnavailableError` detail string, surface an Indonesian-localized toast: title "Layanan AI tidak tersedia", body the server-provided message, action button "Coba lagi" that re-issues the failed request. Hide the raw error JSON from the user. Use the existing toast component (search `pltu-tenayan-full-backup/frontend/src/` for the toast / notification utility — planner identifies the canonical pattern).

### Excel parser verification + regression fixture (D-11..D-13 — closes OPS-03)

- **D-11:** **Proxy samples = `Loading.xlsx`, `Unloading.xlsx`, `Lab_Internal.xlsx`** (already in `pltu-tenayan-full-backup/`). Each is a real production sample at different shapes — `Loading.xlsx` covers receipt parsing, `Unloading.xlsx` covers discharge parsing, `Lab_Internal.xlsx` covers COA parsing. The literal `total penerimaan.xlsx` is NOT yet provided by the operator — deferred to Phase 7 polish.

- **D-12:** **Verification procedure:**
  1. For each of the 3 xlsx files: upload via the corresponding `/api/<mode>/upload-excel` endpoint against the Phase-4 test DB (`pltu_tenayan_test_<sessionid>`).
  2. Assert: HTTP 200 / 201 + N rows ingested where N matches the xlsx's data-row count (header-row-aware).
  3. Cross-check at least 3 deterministic field values per file against the MongoDB-persisted document (e.g., `shipment_code`, `gcv_arb`, `name_of_vessel`).
  4. If a parser path raises or produces wrong-shape data, fix the parser code in `server.py` (file:line documented in the plan).
  5. Discrepancies log committed at `pltu-tenayan-full-backup/docs/audit/EXCEL_PARSER_VERIFICATION.md`.

- **D-13:** **Regression fixture:** create a sanitized subset (~50 rows per mode max) of each real xlsx and commit at `pltu-tenayan-full-backup/backend/tests/fixtures/excel/regression/{loading,unloading,lab_internal}_sample.xlsx`. Sanitization: replace real supplier names + contract numbers with deterministic dummies. The Phase-4 `test_upload_excel.py` is extended with a parametrized test for the regression fixtures.

### AI chat UI design (D-14..D-19 — closes OPS-04 + cross-cuts OPS-02)

- **D-14:** **Canonical collection name = `ai_chat_history`** (per ADR-012, Phase 5 lock-in). Phase 6 read paths in the new chat UI MUST use `ai_chat_history` — never `ai_conversations`. The ROADMAP Phase 6 SC-4 wording (which says `ai_conversations`) is stale; the planner reconciles by writing the canonical name in PLAN.md and noting the reconciliation in the SUMMARY.

- **D-15:** **Cross-session per-user history.** The UI shows ALL conversations belonging to the currently-logged-in user (not just the current session). Filter by `user_id` field in `ai_chat_history`. Recent-first sort order.

- **D-16:** **Layout = sidebar + main panel:**
  - **Sidebar (left)**: scrollable list of conversation entries. Each entry shows: (a) auto-generated title (first ~50 chars of the first user message, fallback "Percakapan tanpa judul"), (b) relative timestamp (e.g., "2 jam yang lalu"). Clicking an entry switches the main panel.
  - **Main panel (right)**: messages in chronological order (oldest at top, newest at bottom) for the selected conversation. Lazy-load older messages when the user scrolls to top.
  - **"Percakapan Baru" button** at the top of the sidebar: creates a new empty conversation, switches to it.
  - On first load: shows the most recent conversation; if user has zero conversations, shows an empty-state message + the new-conversation button.

- **D-17:** **Pagination strategy:** lazy-load older messages 20 at a time on scroll-to-top of main panel. Sidebar conversations are fetched all at once on initial load (assume <100 conversations per user; if grows, polish phase adds pagination there).

- **D-18:** **Backend endpoints needed:**
  - `GET /api/ai/conversations` — list user's conversations (canonical name maps to `ai_chat_history` grouped by `session_id` or `conversation_id`). Returns `[{id, title, last_message_at}]`.
  - `GET /api/ai/conversations/<id>/messages?before=<message_id>&limit=20` — paginated message fetch.
  - `POST /api/ai/conversations` — create new empty conversation, returns `{id}`.
  - `POST /api/ai/conversations/<id>/messages` — send user message; backend calls LLM, persists both user message + AI response to `ai_chat_history`, returns the AI response. Wraps the LLM call in `LLMUnavailableError` retry-with-backoff per D-09.
  - The planner checks `server.py` for any existing AI chat endpoints first — extends them if they exist; creates new if not. Endpoint contract document at `pltu-tenayan-full-backup/docs/audit/AI_CHAT_API.md`.

- **D-19:** **Indonesian-localized error UX (cross-cut with OPS-02):**
  - LLM unavailable (503): toast "Layanan AI tidak tersedia. Silakan coba lagi sebentar." + "Coba lagi" button.
  - Auth expired (401): toast "Sesi habis. Silakan login ulang." + redirect to login.
  - Network error (no response): toast "Tidak terhubung ke server." + "Coba lagi".
  - All toasts use the existing toast component; planner identifies its location.

### Claude's Discretion

- Exact OpenRouter default model ID — planner picks at plan time (likely `anthropic/claude-3-5-sonnet` for cost-quality balance, but `openai/gpt-4o` or `google/gemini-pro-1.5` are valid choices). The choice must support structured JSON output per CONS-blending-ai-output.
- Retry intervals — D-09 specifies 1/2/4s; planner may tune slightly if OpenRouter rate-limit semantics suggest different intervals.
- Indonesian copy details for toast titles / bodies / button labels — planner can refine for consistency with the existing UI tone.
- Title generation: simple substring (first 50 chars of first message) is the default; planner may swap for an LLM-generated title later if that becomes desirable, but NOT in Phase 6 (cost + complexity).
- Whether to migrate `ai_chat_history` schema (e.g., add `conversation_id` field if not already present) — planner inspects current schema first and decides; if schema migration is needed, it must NOT break existing 10 production records.
- Folder/file structure under `frontend/src/` for the new chat UI components — planner picks based on existing convention.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase boundary + requirements
- `.planning/ROADMAP.md` §"Phase 6: Operational Unblocks" — goal + 5 SC + dependencies (Phase 4). Note: SC-4 wording `ai_conversations` is stale; canonical = `ai_chat_history` per ADR-012.
- `.planning/REQUIREMENTS.md` lines 53-56 — OPS-01..04 verbatim text.
- `.planning/PROJECT.md` §"Active" items OPS-01 + OPS-02 + STAB-06 (= OPS-04 per discussion mapping).

### Architectural anchors (Phase-5 locks)
- `.planning/decisions/ADR-012-canonical-ai-chat-history.md` — `ai_chat_history` is canonical (Phase 6 reads MUST use this name).
- `.planning/decisions/ADR-004-jwt-bcrypt-three-role-auth.md` — auth contract for the new chat endpoints (`Depends(get_current_user)` filter for cross-session per-user).
- `.planning/intel/constraints.md` — CONS-blending-ai-output (FakeAIClient + OpenRouter response must be valid JSON parseable by the smart-blending endpoint's `json.loads`).

### Phase-4 carry-forward (the seam Phase 6 plugs into)
- `pltu-tenayan-full-backup/backend/app/ai/client.py` — `AIClient` Protocol + `get_ai_client()` factory with `AI_FAKE=1` branch. Phase 6 swaps the production branch from `EmergentLLMClientWrapper` to `OpenRouterClient`.
- `pltu-tenayan-full-backup/backend/app/ai/emergent_wrapper.py` — current production AI client wrapper (Phase 4 lift). Phase 6 RENAMES this file to `openrouter_client.py` and rewrites the implementation (same Protocol contract, new HTTP backend).
- `pltu-tenayan-full-backup/backend/tests/fakes/ai_client.py` — `FakeAIClient` (Phase 4); Phase 6 does NOT modify, only validates it still satisfies the contract under the new implementation.
- `pltu-tenayan-full-backup/backend/tests/conftest.py` — `_backend_lifecycle` spawns subprocess with `AI_FAKE=1`. No change needed.

### Phase-5 lock-in (collection naming)
- `pltu-tenayan-full-backup/DATABASE_SCHEMA.md` §13.1 — `ai_chat_history` canonical (post-Phase-5 cleanup).
- All Phase-6 read paths to `ai_chat_history` (NEVER `ai_conversations`).

### Code targets (Phase 6 modifies)
- `pltu-tenayan-full-backup/backend/server.py` — (a) smart-blending aggregation field-name fixes; (b) wrap LLM call in retry-with-backoff; (c) new/extended AI conversation endpoints per D-18; (d) `LLMUnavailableError` → HTTP 503 mapping.
- `pltu-tenayan-full-backup/backend/.env` — env-var rename `EMERGENT_LLM_KEY` → `OPENROUTER_API_KEY`.
- `pltu-tenayan-full-backup/backend/.env.example` — sync.
- `pltu-tenayan-full-backup/backend/requirements.txt` — remove `emergentintegrations`.
- `pltu-tenayan-full-backup/frontend/src/` — chat UI components (sidebar + main + toast); planner identifies exact paths.

### Real Excel samples (proxy for OPS-03)
- `pltu-tenayan-full-backup/Loading.xlsx` (184 KB) — receipt parsing proxy.
- `pltu-tenayan-full-backup/Unloading.xlsx` (312 KB) — discharge parsing proxy.
- `pltu-tenayan-full-backup/Lab_Internal.xlsx` (148 KB) — COA parsing proxy.

### Operator runbooks (style precedent)
- `pltu-tenayan-full-backup/MIGRATION_RUNBOOK.md` (Phase 5 deliverable) — operator-runbook style; Phase 6 cutover runbook follows the same shape (Prerequisites / Backup / Apply / Smoke / Rollback / Cleanup).
- `pltu-tenayan-full-backup/backend/tests/TEST-RUNNER.md` — env-var sourcing precedent.

### UI design references
- `pltu-tenayan-full-backup/frontend/src/components/` (planner explores) — existing chat / toast / sidebar component conventions.
- ROADMAP `UI hint: yes` — planner spawns `gsd-ui-phase 6` to produce UI-SPEC.md before PLAN.md (standard flow for UI-hinted phases).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`AIClient` Protocol + `get_ai_client()` factory** (Phase 4) — Phase 6 plugs the new `OpenRouterClient` into this seam. Zero changes to test code; existing 9 AI endpoint tests + LLM-leak guard continue to pass.
- **`FakeAIClient`** — already returns valid CONS-blending-ai-output JSON for the blending endpoint; Phase 6 doesn't touch this.
- **`tests/factories/{smartstock,sumberpemakaian,coa,...}.py`** (Phase 4) — Phase 6 reuses for seeded smart-blending data-correctness tests (D-07).
- **`/api/auth/*`** endpoints — Phase 6 chat endpoints reuse the same auth dependency pattern (`Depends(get_current_user)`) for per-user filter.
- **Existing toast/notification component** — Phase 6 error UX uses it; planner identifies its export path.
- **`/api/ai/query` + `/api/smart-blending/recommend`** endpoints (Phase 4 wired with `Depends(get_ai_client)`) — Phase 6 retry-with-backoff wraps these calls.

### Established Patterns
- **Env-var driven credentials** — `OPENROUTER_API_KEY` follows the same pattern as `EMERGENT_LLM_KEY` did. Memory/test_credentials.md (gitignored) is NOT used for OpenRouter (operator-managed; production-time env source).
- **`AI_FAKE=1` env-var branch** in `get_ai_client()` — preserved verbatim. Phase 6 only swaps the non-fake branch.
- **Two-repo commit boundary** — backend code, frontend code, `.env`, requirements.txt commit to `pltu-tenayan-full-backup/`. ADRs (if any new), SUMMARY.md, STATE.md commit to outer planning repo.
- **Indonesian-localized UI strings** — existing UI is Indonesian (REQ-i18n-indonesian-ui); new chat UI + error toasts MUST match.
- **MADR ADR style** — if Phase 6 needs a new ADR (e.g., ADR-013 documenting the OpenRouter provider choice), it follows the same format as ADR-001..012.

### Integration Points
- **server.py AI endpoint LLM call sites** (2 endpoints — `/api/ai/query` and `/api/smart-blending/recommend`) — wrap each in retry-with-backoff. The current Plan-04-01 `Depends(get_ai_client)` injection remains; only the call site adds the `try/except LLMUnavailableError` shape.
- **server.py aggregation sites** — the data-correctness audit re-greps and verifies each `db.<canonical>.aggregate(...)` call against the actual doc schema. Edits are surgical (field-name replacements).
- **frontend → backend chat endpoints** — new `/api/ai/conversations/*` routes; planner adds them under the existing `/api/ai/` router pattern.
- **DEBT-03 regression gate** (Phase 5 grep gate `test_no_legacy_collection_reads_in_server_py`) — Phase 6 MUST NOT re-introduce legacy collection names. The gate enforces this automatically; planner ensures new code uses canonical names only.

</code_context>

<specifics>
## Specific Ideas

- The user has been explicit since the Phase-4 discussion about wanting OpenRouter. Phase 6 D-01..D-05 implement that wish, using the `AIClient` Protocol seam Phase 4 specifically built to enable this migration without test-suite churn.
- The user accepted the "use existing 3 xlsx as proxy" path for OPS-03 because the literal `total penerimaan.xlsx` has never been provided — the planner does NOT block on file procurement; Phase 6 closes OPS-03 with the 3 proxies + a forward-pointer to Phase 7 polish for the literal file.
- Indonesian-localized error UX (D-10, D-19) is a hard requirement — REQ-i18n-indonesian-ui anchors this; no English strings reach the user.

</specifics>

<deferred>
## Deferred Ideas

### Literal `total penerimaan.xlsx` parser verification
- **Origin:** ROADMAP Phase 6 SC-3 + REQUIREMENTS OPS-03 mention this file by name.
- **Why deferred:** Operator has not yet provided the file; Phase 6 closes OPS-03 against the 3 existing real xlsx samples as proxies.
- **Proposed home:** Phase 7 polish (or a follow-on) once the file is uploaded. The Phase-6 regression-fixture pattern (D-13) is the template — extend with a 4th fixture.

### Multi-provider hybrid LLM routing
- **Origin:** Mentioned in Phase-6 Area-1 discussion as an alternative to single-provider OpenRouter.
- **Why deferred:** Complexity not justified for milestone v1.0. Single-provider OpenRouter satisfies OPS-01 cleanly. Polish phase may revisit if cost / availability becomes an operator concern.

### Cost-aware model routing (cheap-first, premium-fallback)
- **Origin:** Same area.
- **Why deferred:** Premature optimization. Phase 6 picks one default model; operator monitors cost via OpenRouter dashboard; if costs become an issue, polish phase adds routing logic.

### Conversation search / export
- **Origin:** Out-of-scope statement in D-16.
- **Why deferred:** Phase 6 closes OPS-04 with read-only history surfacing. Search / export are net-new features, not unblock work. Phase 8 polish.

### Sidebar pagination
- **Origin:** D-17 assumes <100 conversations per user.
- **Why deferred:** Premature for milestone v1.0 (current production has 10 total `ai_chat_history` records). Polish phase adds pagination if the assumption breaks.

### LLM-generated conversation titles
- **Origin:** D-18 title-generation strategy mentions this as a future option.
- **Why deferred:** Cost + latency overhead not justified for milestone v1.0. Simple substring of first message is sufficient.

### Reviewed Todos (not folded)
- None — `gsd-sdk query todo.match-phase 6` to be re-checked at planning time; this CONTEXT.md captured before todo-match query (no pending todos affect Phase 6 scope per current state).

</deferred>

---

*Phase: 06-operational-unblocks*
*Context gathered: 2026-05-11*
