---
phase: 06
slug: operational-unblocks
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-11
---

# Phase 06 — Validation Strategy

> Derived verbatim from 06-RESEARCH.md §"Validation Architecture". Maps each OPS-NN to verifiable surface.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 0.24.0 (Phase-4 baseline) |
| **Config file** | `pltu-tenayan-full-backup/backend/pytest.ini` |
| **Quick run** | `AI_FAKE=1 .venv/bin/pytest tests/test_smart_blending_data.py tests/test_openrouter_client.py -x -q` |
| **Full suite** | `AI_FAKE=1 .venv/bin/pytest tests/ -x -q` |
| **Frontend smoke** | Manual operator step against http://localhost:3013 |
| **Estimated runtime** | quick <30 s · full ~60-90 s |

---

## Sampling Rate

- **Per task commit:** quick command (focused on the area touched).
- **Per wave merge:** full suite.
- **Pre-cutover gate:** full suite green PLUS 3 manual smoke tests (smart-blending @ GCV 4000/4200/4500, AI chat UI, Indonesian error toast).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | OPS-01 (provider) | T-llm-key-leak / mitigated | `OpenRouterClient.send_message()` returns LLM text via OpenRouter; `Authorization: Bearer ${OPENROUTER_API_KEY}` only from env | unit (respx mock) | `pytest tests/test_openrouter_client.py -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | OPS-01 (factory) | — | `get_ai_client()` returns `OpenRouterClient` when `AI_FAKE` unset; returns `FakeAIClient` when `AI_FAKE=1` | unit | `pytest tests/test_openrouter_client.py::test_factory -x` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | OPS-02 | T-llm-unavailable-bubble | After 3 retries, raises `LLMUnavailableError` → 503 with Indonesian body `{"detail": "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar."}` | unit + integration | `pytest tests/test_openrouter_client.py::test_retry_exhaustion -x` | ❌ W0 | ⬜ pending |
| 06-01-04 | 01 | 1 | OPS-01 (env+deps) | — | `emergentintegrations` removed from requirements.txt; both server.py import sites (lines 19, 2263) cleaned; env-var renamed across all 8 doc files | static | `grep -c emergentintegrations server.py requirements.txt = 0`; `grep -c EMERGENT_LLM_KEY {.env,*.md} = 0` (outside historical references) | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | OPS-01 (data) | T-aggregation-field-drift | `db.smartstock.aggregate($sum: "$total_penerimaan")` returns non-zero against seeded test DB | unit | `pytest tests/test_smart_blending_data.py::test_smartstock_sum -x` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 1 | OPS-01 (data) | T-aggregation-field-drift | `db.sumberpemakaian.aggregate($sum: "$total_pemakaian")` returns non-zero | unit | `pytest tests/test_smart_blending_data.py::test_sumberpemakaian_sum -x` | ❌ W0 | ⬜ pending |
| 06-02-03 | 02 | 1 | OPS-01 (integration) | — | `/api/ai/quick/smart-stock` returns `current_stock != 0` against seeded DB (Phase-5 hotfix coercion still holds for null safety) | integration | `pytest tests/test_smart_blending_data.py::test_smart_stock_endpoint -x` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 2 | OPS-03 | T-parser-discrepancy | `parse_coa_excel(Loading.xlsx)` returns expected row count + 3 deterministic field round-trips into canonical MongoDB collection | unit | `pytest tests/test_upload_excel.py::test_coa_regression_loading -x` | ❌ W0 | ⬜ pending |
| 06-03-02 | 03 | 2 | OPS-03 | T-parser-discrepancy | Same for Unloading.xlsx | unit | `pytest tests/test_upload_excel.py::test_coa_regression_unloading -x` | ❌ W0 | ⬜ pending |
| 06-03-03 | 03 | 2 | OPS-03 | T-parser-discrepancy | Same for Lab_Internal.xlsx | unit | `pytest tests/test_upload_excel.py::test_coa_regression_internal -x` | ❌ W0 | ⬜ pending |
| 06-03-04 | 03 | 2 | OPS-03 (fixtures) | T-pii-leak / mitigated | Sanitized regression fixtures (≤50 rows each; PT names + contract numbers replaced) committed at `backend/tests/fixtures/excel/regression/` | static | `ls backend/tests/fixtures/excel/regression/*.xlsx \| wc -l = 3` | ❌ W0 | ⬜ pending |
| 06-04-01 | 04 | 2 | OPS-04 (list) | — | `GET /api/ai/conversations` returns user's sessions grouped by `session_id`, recent-first, with auto-title from first message | unit | `pytest tests/test_ai_chat_endpoints.py::test_list_conversations -x` | ❌ W0 | ⬜ pending |
| 06-04-02 | 04 | 2 | OPS-04 (messages) | — | `GET /api/ai/conversations/<id>/messages?before=<msg_id>&limit=20` returns paginated messages chronologically | unit | `pytest tests/test_ai_chat_endpoints.py::test_get_messages -x` | ❌ W0 | ⬜ pending |
| 06-04-03 | 04 | 2 | OPS-04 (create) | — | `POST /api/ai/conversations` creates empty session, returns `{id}` | unit | `pytest tests/test_ai_chat_endpoints.py::test_create_conversation -x` | ❌ W0 | ⬜ pending |
| 06-04-04 | 04 | 2 | OPS-04 (send) | T-llm-budget-leak | `POST /api/ai/conversations/<id>/messages` calls LLM via injected `AIClient` + persists both user+AI msg to `ai_chat_history`; under `AI_FAKE=1` zero LLM HTTP calls | integration | `AI_FAKE=1 pytest tests/test_ai_chat_endpoints.py::test_send_message -x` | ❌ W0 | ⬜ pending |
| 06-05-01 | 05 | 3 | OPS-04 (UI) | — | 8 chat components per UI-SPEC render; Layout.js nav has "Riwayat AI" entry; route `/ai/chat` works | manual smoke | (operator visits http://localhost:3013/ai-chat) | ❌ W0 | ⬜ pending |
| 06-05-02 | 05 | 3 | OPS-02 (UI) | — | Indonesian error toast appears on simulated 503; "Coba lagi" button retries failed request; SmartBlendingPage.js:71 English toast localized | manual smoke | (operator triggers + verifies) | ❌ W0 | ⬜ pending |
| 06-06-01 | 06 | 4 | OPS-04 (cutover) | T-prod-bypass | Operator rotates `OPENROUTER_API_KEY` into `/home/damnation/emits/pltu-tenayan-full-backup/backend/.env`, kills old uvicorn, restarts; `/api/health` 200 | manual checkpoint | (see Manual-Only Verifications) | ❌ W0 | ⬜ pending |
| 06-06-02 | 06 | 4 | OPS-01 (smoke) | — | Smart Blending AI returns successful recommendation at target GCV 4000/4200/4500 (3 manual `curl` calls; response valid JSON) | manual checkpoint | (see Manual-Only) | ❌ W0 | ⬜ pending |
| 06-06-03 | 06 | 4 | OPS-04 (smoke) | — | Operator loads AI Chat page, creates new conversation, sends message, sees AI response, switches conversation, sees history | manual checkpoint | (see Manual-Only) | ❌ W0 | ⬜ pending |
| 06-01..04 | — | — | Regression | — | Existing AI endpoint tests still pass after OpenRouter migration | regression | `AI_FAKE=1 pytest tests/test_ai_endpoints.py -x` | ✅ exists | ⬜ pending |
| 06-01..04 | — | — | DEBT-03 gate | — | No legacy collection name reads (Phase-5 lock) | regression | `pytest tests/test_clean_checkout_gate.py -x` | ✅ exists | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Wave 0 = prerequisite scaffolding before Wave-2 plans can start. Plan 06-01 + 06-02 (Wave 1) produce most of these.

- [ ] `pltu-tenayan-full-backup/backend/app/ai/openrouter_client.py` — implements AIClient Protocol; httpx + 3-retry; LLMUnavailableError
- [ ] `pltu-tenayan-full-backup/backend/app/ai/client.py` — updated factory branches on `AI_FAKE`; default returns OpenRouterClient
- [ ] `pltu-tenayan-full-backup/backend/server.py` — emergentintegrations imports removed (lines 19 + 2263), 7 aggregation field-names fixed, LLMUnavailableError handler wired, env var read from `OPENROUTER_API_KEY` / `OPENROUTER_DEFAULT_MODEL`
- [ ] `pltu-tenayan-full-backup/backend/.env` + `.env.example` — env var renamed
- [ ] `pltu-tenayan-full-backup/backend/requirements.txt` — `emergentintegrations` removed
- [ ] `pltu-tenayan-full-backup/backend/tests/test_openrouter_client.py` — 3+ tests (factory, send_message, retry_exhaustion)
- [ ] `pltu-tenayan-full-backup/backend/tests/test_smart_blending_data.py` — 3 tests (smartstock sum, sumberpemakaian sum, integration smart-stock endpoint)
- [ ] `pltu-tenayan-full-backup/backend/tests/test_upload_excel.py` — extended with 3 COA regression tests
- [ ] `pltu-tenayan-full-backup/backend/tests/fixtures/excel/regression/{loading,unloading,lab_internal}_sample.xlsx` — sanitized ≤50-row subsets
- [ ] `pltu-tenayan-full-backup/backend/tests/test_ai_chat_endpoints.py` — 4 tests (list, get_messages, create, send_message)
- [ ] `pltu-tenayan-full-backup/frontend/src/pages/AIChatPage.js` (+ 7 sub-components per UI-SPEC component inventory)
- [ ] `pltu-tenayan-full-backup/frontend/src/components/Layout.js` — nav link "Riwayat AI" + route registration in App.js

*Existing infra preserved verbatim:*
- Phase-4 conftest (`_backend_lifecycle` on :18013, `_seed_baseline_data`, factories, helpers)
- Phase-4 tests/fakes/ai_client.py (FakeAIClient — Phase 6 verifies still satisfies new client signature)
- Phase-5 ADR-012 canonical name (no `ai_conversations` references)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| OPENROUTER_API_KEY rotated into prod | OPS-01 cutover | Filesystem state + operator action | Operator edits `.env`, sets `OPENROUTER_API_KEY=<OPENROUTER_API_KEY>` from their OpenRouter dashboard; `pkill uvicorn`; restart per LOCAL_SETUP.md §VPS Service Recovery; `curl /api/health` 200 |
| Smart-blending recommendation at 3 GCV targets | OPS-01 SC-1 | Live LLM call against real OpenRouter; non-deterministic response | Operator runs 3× `curl POST /api/smart-blending/recommend` with `{target_gcv: 4000}`, `{target_gcv: 4200}`, `{target_gcv: 4500}` body; each response is `json.loads`-parseable + contains non-empty `blend` array |
| AI Chat UI live smoke | OPS-04 SC-4 | Browser-only UX | Operator visits http://localhost:3013/ai-chat: empty-state appears for fresh user → click "Percakapan Baru" → type message → AI response renders → switch conversations → history persisted |
| Indonesian error toast | OPS-02 | Browser UX | Operator temporarily sets invalid OPENROUTER_API_KEY → sends chat → confirms toast "Layanan AI tidak tersedia" + "Coba lagi" button — NOT raw error JSON |

---

## Validation Sign-Off

- [ ] All tasks have automated verify OR Manual-Only entry
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify (Plan 06-06 cutover is the only manual-heavy plan, by design — autonomous=false)
- [ ] Wave 0 covers all MISSING references (12 deliverables)
- [ ] No watch-mode flags
- [ ] Feedback latency <90 s for automated paths
- [ ] `nyquist_compliant: true` set in frontmatter (flip after PLAN.md files produced)

**Approval:** pending
