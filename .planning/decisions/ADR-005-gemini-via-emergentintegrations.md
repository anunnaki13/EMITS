# ADR-005: Google Gemini (gemini-2.5-flash) via emergentintegrations as v1 AI Provider

## Status

Accepted (locked, 2026-05-10) — promoted from IMPLICIT-005.

## Context

EMITS ships an **AI Intelligence Agent** with seven analysis modules — `general`, `blending`, `boiler` (boiler_risk), `contract`, `logistics`, `smart-stock`, `coa` — plus six "quick" endpoints (`/api/ai/quick/blending-suggestion`, `/boiler-alerts`, `/contract-status`, `/logistics-losses`, `/smart-stock`, `/coa-alerts`) and a session-memory endpoint set under `/api/ai/sessions`. This is `REQ-ai-intelligence-agent` (validated/shipped) and is one of the highest-value features per the operational stakeholders at PLTU Tenayan.

The LLM provider is **Google Gemini** accessed through the **`emergentintegrations`** Python SDK. Default model is `gemini-2.5-flash`. Per-user keys override the default; `EMERGENT_LLM_KEY` env var is the fallback shared key. The configuration is exposed via `GET/PUT /api/ai/settings` (CONS-ai-query-endpoint).

At plan time, Smart Blending AI is operationally degraded — `BudgetExceededError` from the Universal LLM Key budget — but the *code path* is correct. The provider choice is not the cause; the budget is. PROJECT.md's "Out of Scope" explicitly defers multi-provider abstraction; OPS-01 + OPS-02 in the active backlog track budget restoration and graceful UI error surfacing.

This ADR locks the v1 provider choice so future plans cite it directly. ADR-005 does NOT lock the SDK abstraction layer, which is a v2 conversation (a future `LLM-V2-01`-class plan).

## Decision

For the v1 AI Intelligence Agent, the LLM provider is **Google Gemini** accessed via the **`emergentintegrations`** Python SDK. The default model is **`gemini-2.5-flash`**.

Locked clauses:

- **Provider:** Google Gemini (single-provider for v1).
- **SDK:** `emergentintegrations==0.1.0` (with transitive `google-genai==1.59.0`, `google-generativeai==0.8.6`).
- **Default model:** `gemini-2.5-flash` (CONS-ai-query-endpoint, AISettings default).
- **Key resolution order:** per-user key from `user_settings.custom_api_key` → `EMERGENT_LLM_KEY` env var fallback.
- **Settings surface:** `GET/PUT /api/ai/settings` body `{ custom_api_key?, llm_provider, llm_model }` — `llm_provider` defaults to `gemini`, `llm_model` to `gemini-2.5-flash`.
- **Wiring:** the `LlmChat` and `UserMessage` classes from `emergentintegrations.llm.chat` are imported at the top of `backend/server.py` and instantiated inside `/api/ai/query` (no separate service module today; `backend/services/` exists but contains only `coa_reconciliation.py` and `excel_parser.py` — there is no `services/ai_intelligence.py`).

## Consequences

**Positive:**

- One SDK, one provider — operational surface is small; no provider-routing logic to maintain in v1.
- `emergentintegrations` already abstracts the Gemini-specific request/response shape behind a `LlmChat` interface, so when v2 needs a multi-provider rewrite it has a known seam (the import line + `LlmChat()` constructor are the only contact points in `server.py`).
- Per-user `custom_api_key` allows operators with their own Google AI key to bypass the shared budget — a pragmatic pre-mitigation for the BudgetExceededError situation.
- `gemini-2.5-flash` is fast and cheap enough for the seven analysis modules' query patterns (mostly summarization + small JSON extraction over 6-month vessel/barge/trucking quality + smart-stock context).

**Negative / accepted tradeoffs:**

- **When the Universal LLM Key budget is exhausted, calls fail with `BudgetExceededError`. This is an environmental / billing concern, not a code defect.** Phase 6 (OPS-01, OPS-02) tracks budget restoration and graceful UI error surfacing. Until then, smart-blending recommendations are operationally degraded; the frontend currently surfaces a 500 toast which is technically correct per CONS-auth-header's "500 internal/AI integration error" mapping.
- Single-provider lock-in for v1 — switching provider later requires rewriting the LLM call sites or extending `emergentintegrations`'s abstraction. Mitigated by the SDK's pre-existing `LlmChat` boundary.
- Gemini's response format for tool-use / structured-output is provider-specific; the JSON-shape contract (CONS-blending-ai-output, CONS-ai-query-endpoint) is enforced by careful prompt engineering rather than by a vendor-neutral schema-output API.
- `emergentintegrations` is a less-known SDK; transitive Google deps (`google-genai`, `google-generativeai`) are pinned in `requirements.txt` to avoid surprise updates breaking the chat interface.

## Alternatives Considered

- **OpenAI direct (gpt-4o / gpt-4o-mini)** — rejected for v1. `emergentintegrations` already abstracts; switching providers is v2 LLM-V2-01 scope. No current operator complaint about model quality; budget exhaustion is an account problem, not a model problem.
- **Anthropic Claude direct** — rejected for v1, same reason.
- **Local LLM (Ollama / llama.cpp on the same VPS)** — rejected. The VPS does not have GPU; small-model on CPU inadequate for the prompt complexity in blending / COA modules where 6-month context windows + structured output matter.
- **OpenRouter / LiteLLM gateway as a multi-provider abstraction** — considered, deferred to v2. Adds an extra hop and a config surface that doesn't pay back at the current single-provider operational reality. PROJECT.md explicitly defers multi-provider abstraction.

## References

- **Source IMPLICIT line:** `.planning/PROJECT.md` "Constraints" section, IMPLICIT-005 row (line 94: "AI provider (LOCKED operationally, implicit/inherited): Google Gemini (`gemini-2.5-flash`) via `emergentintegrations`; falls back to `EMERGENT_LLM_KEY` when no per-user key. Per IMPLICIT-005. Operational dependency — not a code defect when budget exhausted.").
- **Code anchors (proof in effect):**
  - `pltu-tenayan-full-backup/backend/server.py:19` — `from emergentintegrations.llm.chat import LlmChat, UserMessage`
  - `pltu-tenayan-full-backup/backend/server.py:2260-2261` — `# ==================== AI INTELLIGENCE AGENT ====================` section header + re-import line
  - `pltu-tenayan-full-backup/backend/server.py:2619` — `@api_router.post("/ai/query")` (the main AI query endpoint)
  - `pltu-tenayan-full-backup/backend/server.py:2714` — `@api_router.get("/ai/settings")`
  - `pltu-tenayan-full-backup/backend/requirements.txt:20` — `emergentintegrations==0.1.0`
  - `pltu-tenayan-full-backup/backend/requirements.txt:33` — `google-genai==1.59.0`
  - `pltu-tenayan-full-backup/backend/requirements.txt:34` — `google-generativeai==0.8.6`
  - `pltu-tenayan-full-backup/backend/services/` — present but contains only `coa_reconciliation.py` + `excel_parser.py`; **no dedicated AI service module today** (drift note: a future plan may introduce `services/ai_intelligence.py` to host the `LlmChat` instantiation).
- **Related constraints:** `.planning/intel/constraints.md` → CONS-ai-query-endpoint (endpoint contract + default `gemini` / `gemini-2.5-flash`), CONS-smart-blending-endpoint (operational note: "depends on LLM budget; failure when budget exhausted is environmental, not a code defect").
- **Sibling docs:** PROJECT.md "Out of Scope" (multi-provider abstraction explicitly deferred), `pltu-tenayan-full-backup/Smart_Blending_AI_Formula.md` (Smart Blending math contract — orthogonal but consumed by the blending AI module).
