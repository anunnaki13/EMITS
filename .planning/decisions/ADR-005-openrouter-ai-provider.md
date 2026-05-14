# ADR-005: OpenRouter As The AI Provider

## Status

Accepted (locked, 2026-05-14) — supersedes the original Gemini SDK decision.

## Context

EMITS ships an AI Intelligence Agent with domain modules for general analysis,
blending, boiler risk, contract, logistics, smart stock, and COA
reconciliation. The application now routes production AI calls through the
`AIClient` protocol and `OpenRouterClient` implementation in `backend/app/ai/`.

The old provider-specific wrapper and generated SDK folder have been removed.
The active runtime contract is OpenRouter over HTTP, with test isolation through
`AI_FAKE=1`.

## Decision

Use OpenRouter as the production LLM provider for EMITS.

Locked clauses:

- **Provider:** OpenRouter.
- **Client:** `backend/app/ai/openrouter_client.py`.
- **Default model:** `openai/gpt-4o-mini`, configurable via
  `OPENROUTER_DEFAULT_MODEL`.
- **Default key:** `OPENROUTER_API_KEY`, never committed.
- **Settings surface:** `GET/PUT /api/ai/settings` remains the user-facing
  configuration surface.
- **Test seam:** `AI_FAKE=1` returns `FakeAIClient` and must not consume LLM
  budget or call the network.

## Consequences

**Positive:**

- Removes the stale vendor-specific wrapper and generated local SDK artifacts.
- Keeps the production client small and explicit through `httpx`.
- Preserves the `AIClient` protocol seam for tests and future provider changes.
- Makes the active environment variables match current deployment practice.

**Tradeoffs:**

- OpenRouter availability, account quota, and selected model health are now the
  operational dependencies for AI features.
- Provider-specific response behavior still needs guardrails in prompts and
  parsing, especially for JSON smart-blending sessions.

## References

- `backend/app/ai/client.py` — provider factory and `AI_FAKE=1` seam.
- `backend/app/ai/openrouter_client.py` — production OpenRouter client.
- `backend/routers/ai_intelligence.py` — AI endpoints using `AIClient`.
- `backend/tests/fakes/ai_client.py` — deterministic test client.
- `backend/tests/test_ai_endpoints.py` — AI endpoint contract tests.
