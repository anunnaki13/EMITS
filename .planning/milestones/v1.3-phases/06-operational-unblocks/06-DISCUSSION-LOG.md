# Phase 06: Operational Unblocks - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-11
**Phase:** 06-operational-unblocks
**Areas discussed:** LLM provider strategy, Smart Blending data correctness, Excel parser verification, AI chat UI design

---

## LLM provider strategy (OPS-01)

| Option | Description | Selected |
|--------|-------------|----------|
| OpenRouter migration | Swap implementation di balik AIClient Protocol Phase 4. Rename LegacyLLMClient → OpenRouterClient. LEGACY_LLM_KEY → OPENROUTER_API_KEY. Test seam tidak berubah. | ✓ |
| Gemini budget refill saja | Operator beli kuota LEGACY_LLM_KEY. Same code, same vendor. Vendor lock-in tetap. | |
| Hybrid — OpenRouter primary, Gemini fallback | Dual provider routing. Complex testing + monitoring. | |

**User's choice:** OpenRouter migration (Recommended)
**Notes:** Selaras dengan permintaan eksplisit user sejak Phase 4 discussion. AIClient Protocol seam (Phase 4 D-04..D-07) was specifically designed to enable this migration without test churn. Default model picked at planning time; must support structured JSON output per CONS-blending-ai-output.

---

## Smart Blending data correctness (OPS-01 follow-on)

| Option | Description | Selected |
|--------|-------------|----------|
| Bundle ke OPS-01 | Audit ALL smart-blending-related aggregations + fix field-name mismatches + unit test per aggregation. SC-1 requires meaningful recommendation, which requires correct data path. | ✓ |
| Separate post-OPS-01 plan | OPS-01 = provider switch only. Data correctness = separate plan. Risk: OPS-01 closed but smart blending still returns garbage. | |
| Skip — accept zero-data state | Phase 6 closes OPS-01 if LLM call succeeds + shape valid, regardless of recommendation content. Defer correctness to polish. | |

**User's choice:** Bundle ke OPS-01 (Recommended)
**Notes:** Phase 5 CP2 surfaced the field-mismatch in `/api/ai/quick/smart-stock`. Audit covers smartstock + sumberpemakaian aggregations + blending suggestion endpoint. Use mongosh `db.<col>.findOne()` to confirm schema before fix.

---

## Excel parser verification (OPS-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Pakai 3 existing xlsx sebagai proxy | Loading.xlsx + Unloading.xlsx + Lab_Internal.xlsx adalah real production samples. Verify parsers terhadap ketiganya. Document verification log + sanitize subset jadi regression fixture (~50 rows/mode). | ✓ |
| Operator upload total penerimaan.xlsx sekarang | Pause planning sampai file ada di VPS. | |
| Defer OPS-03 entirely ke post-milestone | Phase 6 focus OPS-01/02/04. | |

**User's choice:** Pakai 3 existing xlsx sebagai proxy
**Notes:** Literal `total penerimaan.xlsx` belum diberikan operator → Phase 7 polish. Discrepancy fixes go into parser code; regression fixture = sanitized subset committed to backend/tests/fixtures/excel/regression/.

---

## AI chat UI design (OPS-04, UI hint=yes)

| Option | Description | Selected |
|--------|-------------|----------|
| Cross-session per-user, sidebar+main layout | Left sidebar: list conversations (recent-first, auto-title); Main panel: messages dalam selected. Lazy-load older on scroll. New conversation button. Indonesian-localized budget-exhausted toast + retry. Standard chat UI pattern. | ✓ |
| Session-only (no history persistence in UI) | Chat hanya tampilkan current session. ai_chat_history populated tapi tidak surface — tidak fully memenuhi OPS-04. | |
| Timeline single-view (no conversation grouping) | Single chronological scroll. Easier implement, awkward UX for multiple topics. | |

**User's choice:** Cross-session per-user, sidebar+main layout (Recommended)
**Notes:** Reads from canonical `ai_chat_history` (ADR-012; the ROADMAP SC-4 mention of `ai_conversations` is stale and gets reconciled at planning time). Auto-generated titles from first ~50 chars of first user message. Indonesian error toasts (REQ-i18n-indonesian-ui).

---

## Claude's Discretion

- OpenRouter default model identifier (anthropic/claude-3-5-sonnet vs openai/gpt-4o vs google/gemini-pro-1.5) — planner picks based on JSON-output reliability + cost.
- Retry intervals (1/2/4s default) — planner may tune.
- Indonesian copy details for error toasts — planner refines.
- Conversation title generation — substring is default; planner may swap for LLM-generated later (NOT Phase 6 scope).
- ai_chat_history schema migration (e.g., add conversation_id field if absent) — planner inspects + decides; existing 10 production records must not break.
- Frontend folder/file structure for chat UI components — planner picks per existing convention.

## Deferred Ideas

- **Literal `total penerimaan.xlsx`** parser verification → Phase 7 polish once operator provides file.
- **Multi-provider hybrid LLM routing** → future polish phase if cost/availability becomes concern.
- **Cost-aware model routing** (cheap-first, premium-fallback) → polish phase.
- **Conversation search / export** → Phase 8 polish.
- **Sidebar pagination** → polish phase if >100 conversations/user.
- **LLM-generated conversation titles** → polish phase (cost + latency).
