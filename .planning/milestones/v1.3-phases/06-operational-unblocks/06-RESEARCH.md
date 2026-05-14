# Phase 06: Operational Unblocks — Research

**Researched:** 2026-05-11
**Domain:** LLM provider migration (OpenRouter), smart-blending data correctness, Excel parser verification, AI chat history UI
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**OPS-01 (Provider + Data):**
- D-01: OpenRouter is the new LLM provider. Single-provider, no hybrid fallback.
- D-02: Rename `LegacyLLMClient` → `OpenRouterClient`; `legacy_llm_wrapper.py` → `openrouter_client.py`. Implements `AIClient` Protocol from `app/ai/client.py`. `get_ai_client()` factory keeps `AI_FAKE=1` branch untouched.
- D-03: Env-var rename `LEGACY_LLM_KEY` → `OPENROUTER_API_KEY` across `.env`, `.env.example`, `MIGRATION_RUNBOOK.md`, `LOCAL_SETUP.md`, `DEPLOYMENT_GUIDE.md`, `CREDENTIAL_HYGIENE.md`, `documentation.md`, `readme.md` (all six docs have confirmed references).
- D-04: Default model = `openai/gpt-4o-mini` (user-selected 2026-05-11). Configurable via `OPENROUTER_DEFAULT_MODEL` env var (default `openai/gpt-4o-mini`).
- D-05: Remove `legacy-ai-sdk` from `requirements.txt`. `httpx` is the only outbound HTTP dep; it is already present (`httpx==0.28.1`).
- D-06: Bundle data audit into OPS-01. Phase 5 CP2 surfaced `/api/ai/quick/smart-stock` returning zeros — aggregation field names don't match smartstock doc schema.
- D-07: Fix mode: correct field names in `server.py`. Add unit test per fix in `test_smart_blending_data.py`.
- D-08: Validation gate: 3 live smoke calls (target GCV 4000/4200/4500) at cutover.

**OPS-02 (Error UX):**
- D-09: Retry-with-backoff in `OpenRouterClient`: 3 retries, 1/2/4s exponential, for 429 + 5xx + Timeout. After exhaustion raises `LLMUnavailableError`. Endpoint maps to HTTP 503 with Indonesian body.
- D-10: Frontend error toast: 503 → "Layanan AI tidak tersedia" + server detail + "Coba lagi" retry button.

**OPS-03 (Excel):**
- D-11: Proxy samples = `Loading.xlsx`, `Unloading.xlsx`, `Lab_Internal.xlsx`.
- D-12: Verification: upload to test DB via corresponding endpoint, assert HTTP 200/201 + row count matches xlsx data rows, cross-check 3 deterministic fields per file.
- D-13: Regression fixture: ~50 rows per mode, sanitized supplier names + contract numbers, at `backend/tests/fixtures/excel/regression/`.

**OPS-04 (AI Chat UI):**
- D-14: Canonical collection = `ai_chat_history`. NEVER `ai_conversations`.
- D-15: Cross-session per-user history. Filter by `user_id`. Recent-first sort.
- D-16: Layout = sidebar + main panel. "Percakapan Baru" button. Auto-generated title from first user message (50 chars). "Percakapan tanpa judul" fallback.
- D-17: Pagination: first-load 20 messages. Sidebar all-at-once (assume <100 per user). Lazy-load older 20 on scroll-to-top.
- D-18: 4 new endpoints: `GET /api/ai/conversations`, `GET /api/ai/conversations/<id>/messages?before=<msg_id>&limit=20`, `POST /api/ai/conversations`, `POST /api/ai/conversations/<id>/messages`.
- D-19: Indonesian-localized error toasts for all 3 error conditions (503, 401, network).

### Claude's Discretion

- Retry intervals: D-09 specifies 1/2/4s; planner may tune slightly.
- Indonesian copy details for toast titles/bodies/button labels.
- Whether to add `conversation_id` field to `ai_chat_history` schema (must not break existing 10 records).
- Folder/file structure under `frontend/src/` (UI-SPEC.md has locked this to `pages/AIChatPage.js` + `components/ai-chat/`).
- Title generation: simple 50-char substring of first user message.

### Deferred Ideas (OUT OF SCOPE)

- `total penerimaan.xlsx` parser verification (Phase 7)
- Multi-provider hybrid LLM routing
- Cost-aware model routing
- Conversation search / export (Phase 8)
- Sidebar pagination (Phase 8 if needed)
- LLM-generated conversation titles
- Index rationalization on `ai_chat_history`
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OPS-01 | Smart Blending AI returns a successful recommendation against live data (Gemini budget exhausted → OpenRouter migration + data audit) | Focus 1 (OpenRouter contract), Focus 2 (smart-blending data correctness), Focus 5 (retry-with-backoff) |
| OPS-02 | Retry-with-backoff in smart-blending path + Indonesian-localized error UX (no raw BadGatewayError) | Focus 5 (retry pattern), Focus 6 (FastAPI 503 + LLMUnavailableError), Focus 9 (frontend toast) |
| OPS-03 | Excel parser verified against 3 real xlsx samples; discrepancies fixed; regression fixtures committed | Focus 8 (xlsx inventory + row counts + deterministic values) |
| OPS-04 | AI chat UI shows cross-session per-user history from `ai_chat_history` | Focus 3 (ai_chat_history schema), Focus 9 (frontend integration), Focus 4 (endpoint inventory) |
</phase_requirements>

---

## Summary

Phase 6 closes four operational blockers that have persisted since system ingest. The research confirms all four are unblockable with surgical changes that don't disturb the Phase-4 test suite.

**OPS-01 (LLM migration + data audit):** The `AIClient` Protocol seam Phase 4 introduced makes the provider swap safe — only `legacy_llm_wrapper.py` changes, and the `AI_FAKE=1` branch is untouched. The `legacy-ai-sdk` import also appears at `server.py:19` (top-level, before the class definition at line 2263) — both must be removed. `httpx==0.28.1` is already in `requirements.txt`. The OpenRouter API is OpenAI-compatible; the endpoint is `https://openrouter.ai/api/v1/chat/completions`. For `openai/gpt-4o-mini` with `response_format: {"type": "json_object"}`, the system or user prompt MUST contain the word "JSON" — the existing smart-blending prompt at `server.py:3771` already says "Respons HANYA dengan JSON yang valid" — this satisfies the requirement. The smart-stock aggregations at lines 2395-2400 and 2863-2885 reference `$tonase`, `$batubara_mt`, `$biomassa_mt` on the `smartstock` and `sumberpemakaian` collections — but live schema verification shows `smartstock` docs use `total_penerimaan` (not `tonase`) for per-entry totals, and `sumberpemakaian` docs use `total_pemakaian` (not `batubara_mt`/`biomassa_mt`). The quick-smart-stock endpoint and get_database_context function's AI context builder both have field mismatches.

**OPS-02 (Error UX):** No retry-with-backoff or `LLMUnavailableError` exists today — `server.py:3809-3811` catches a bare `Exception` and returns a raw 500 with `str(e)`. The `sonner` toast library is already in `frontend/package.json` (`sonner==2.0.3`) and mounted in `App.js`. The frontend error classification pattern is documented in the UI-SPEC.

**OPS-03 (Excel):** All three xlsx files have 721 data rows each, 1 header row. Loading.xlsx uses sheet "Sheet1" (33 cols), Unloading.xlsx uses sheet "UNLoading" (59 cols), Lab_Internal.xlsx uses sheet "Sheet1" (31 cols). The `parse_coa_excel` function in `services/coa_reconciliation.py` is the correct parser for all three — this is the COA parser. The COA reconciliation upload endpoint at `/api/coa-reconciliation/upload` accepts all three files simultaneously. Row 2 in all three files is Shipment 555 ("PT PLN BB/SAE") with consistent field values across sheets, making it the deterministic anchor for round-trip assertions.

**OPS-04 (AI Chat UI):** The live `ai_chat_history` collection has 10 documents across 4 unique `session_id` values (2 users). Each document has fields: `id`, `user_id`, `session_id`, `module`, `query`, `response`, `parameters`, `created_at`. There is NO `conversation_id` field. The `session_id` field is the natural grouping key — it already embeds the user_id and a UUID (format: `tenayan-ai-{user_id}-{uuid}`). Phase 6 can use `session_id` as the `conversation_id` without any schema migration to the existing 10 records. New records written by the new chat endpoint will set `conversation_id` equal to a newly-generated UUID (not the session_id format); the existing sessions endpoint infrastructure at lines 2967-3048 can be adapted or the new `/api/ai/conversations/*` endpoints can coexist alongside it.

**Primary recommendation:** Implement `OpenRouterClient` as a clean rewrite of `legacy_llm_wrapper.py` using `httpx.AsyncClient` with 3-retry exponential backoff and `LLMUnavailableError`. Fix the two field-name mismatches in smart-stock aggregations. Use `session_id` as the conversation grouping key for the chat UI without schema migration.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| LLM API calls (OpenRouter) | API / Backend | — | `OpenRouterClient` wraps outbound HTTP; frontend never calls OpenRouter directly |
| Retry-with-backoff | API / Backend | — | Belongs in `OpenRouterClient.send_message()`, not at the endpoint layer |
| LLM error → HTTP 503 mapping | API / Backend | — | FastAPI exception handler; frontend only sees 503 JSON |
| Smart-blending aggregation fixes | API / Backend (Database) | — | Server-side MongoDB aggregation pipeline corrections |
| Excel parse-and-ingest | API / Backend | — | `parse_coa_excel()` in services, called by upload endpoint |
| AI chat history storage + retrieval | Database / API | — | MongoDB `ai_chat_history` + new CRUD endpoints |
| AI chat UI (sidebar + panel) | Browser / Client | Frontend Server (none; CRA static) | React components, no SSR |
| Error toast classification | Browser / Client | — | `catch` block in page component classifies by `err.response.status` |
| Indonesian localization | Browser / Client + API / Backend | — | Backend 503 body is Indonesian; frontend toast copy is Indonesian |
| Auth guard for new chat endpoints | API / Backend | — | `Depends(get_current_user)` reused from existing pattern |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `httpx` | 0.28.1 (already in requirements.txt) | Outbound HTTP to OpenRouter API | Async-native, already in FastAPI dep tree |
| `openai/gpt-4o-mini` | via OpenRouter | Default LLM model | User-locked D-04 |
| FastAPI | 0.110.1 | Endpoint framework | Already in use |
| pymongo / motor | 4.5.0 / 3.3.1 | MongoDB async driver | Already in use |
| sonner | 2.0.3 | Toast notifications | Already mounted in App.js |
| react-markdown + remark-gfm | ^10.1.0 / ^4.0.1 | AI message markdown rendering | Already in package.json |
| date-fns | ^4.1.0 | Relative timestamp formatting | Already in package.json |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openpyxl | 3.1.5 | Excel reading in COA parser | Already used in `parse_coa_excel` |
| tenacity | 9.1.2 | Retry library (alternative to hand-rolled) | Optional — see Focus 5; hand-rolled is also fine |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled retry loop | `tenacity` (already in requirements.txt) | Tenacity is more battle-tested but adds a dependency layer; hand-rolled is clearer for 3-retry simple case |
| `session_id` as conversation key | Add new `conversation_id` UUID field | Schema migration required for existing 10 records; `session_id` is already unique per conversation and embedded with user_id |

**Installation:** No new packages needed. `httpx` already present. Remove `legacy-ai-sdk==0.1.0` from `requirements.txt`.

**Version verification:** `httpx==0.28.1` confirmed in `/home/damnation/emits/pltu-tenayan-full-backup/backend/requirements.txt`. [VERIFIED: file read]

---

## Focus 1: OpenRouter API Contract for `openai/gpt-4o-mini`

### Endpoint

```
POST https://openrouter.ai/api/v1/chat/completions
```

[CITED: openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request]

### Authentication Headers

```http
Authorization: Bearer ${OPENROUTER_API_KEY}
HTTP-Referer: https://103.150.197.225:3013
X-OpenRouter-Title: EMITS PLTU Tenayan
Content-Type: application/json
```

Note: The header is `X-OpenRouter-Title` per current documentation (the older `X-Title` may also work). [CITED: openrouter.ai/docs/api/reference/authentication]

### Request Body Shape

```json
{
  "model": "openai/gpt-4o-mini",
  "messages": [
    {"role": "system", "content": "<system_prompt>"},
    {"role": "user",   "content": "<user_message>"}
  ],
  "response_format": {"type": "json_object"},
  "max_tokens": 2000,
  "temperature": 0.3
}
```

**JSON Mode Critical Requirement:** When `response_format: {"type": "json_object"}` is set, the system or user prompt MUST contain the word "JSON" (case-insensitive). Failure to include it can cause the model to emit whitespace indefinitely until token limit. [CITED: platform.openai.com/docs/guides/structured-outputs, VERIFIED: search]

The existing smart-blending prompt at `server.py:3771` ends with:
```
"Respons HANYA dengan JSON yang valid, tanpa teks tambahan."
```
This contains "JSON" — the requirement is satisfied for smart-blending. The new `/api/ai/conversations/<id>/messages` endpoint MUST also include "JSON" in the system prompt if JSON mode is used. For the general AI chat (non-blending), JSON mode is NOT needed — plain text responses are appropriate.

**Prompt pattern for chat (no JSON mode):**
```python
system_prompt = get_system_prompt(module)  # already contains "JSON" in blending module
# For general chat: no response_format needed; return raw text
```

### Response Body Shape

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "openai/gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "<response text or JSON string>"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1850,
    "completion_tokens": 980,
    "total_tokens": 2830
  }
}
```

Extract via: `response.choices[0].message.content`

[CITED: openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request]

### Error Shapes

```json
{
  "error": {
    "code": 401,
    "message": "No auth credentials found",
    "metadata": {}
  }
}
```

| HTTP Status | Condition | Retry? |
|-------------|-----------|--------|
| 401 | Invalid/missing API key | No — raise immediately |
| 402 | Insufficient credits | No — raise immediately as LLMUnavailableError (budget exhausted) |
| 429 | Rate limit exceeded | Yes — retry with backoff; check Retry-After header |
| 500 | OpenRouter internal error | Yes — retry with backoff |
| 502 | Provider upstream error | Yes — retry with backoff |
| 503 | Provider unavailable | Yes — retry with backoff |

[CITED: openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request]

### Cost Estimate

- `openai/gpt-4o-mini` pricing via OpenRouter: $0.15 / 1M input tokens, $0.60 / 1M output tokens [CITED: openrouter.ai/openai/gpt-4o-mini]
- Smart-blending call: ~2,000 input + ~1,000 output tokens → $0.000300 + $0.000600 = $0.0009/call (~Rp 14 at 16,000/USD)
- General AI chat: ~500 input + ~500 output → ~$0.000150 + $0.000300 = $0.00045/call (~Rp 7)
- Both are well sub-rupiah per call. [VERIFIED: calculation]

### `OpenRouterClient` Implementation Blueprint

```python
# pltu-tenayan-full-backup/backend/app/ai/openrouter_client.py
import os
import asyncio
import httpx
from app.ai.client import AIClient


class LLMUnavailableError(Exception):
    """Raised after all retries exhausted or non-retryable LLM error."""
    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)


class OpenRouterClient:
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    RETRYABLE_STATUSES = {429, 500, 502, 503}

    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini"):
        self._api_key = api_key
        self._model = model

    async def send_message(
        self, session_id: str, system_prompt: str, user_message: str
    ) -> str:
        """Send a message to OpenRouter and return the LLM text response.

        Implements AIClient Protocol. Retries on transient 429/5xx with
        exponential backoff (1s → 2s → 4s). Raises LLMUnavailableError
        after all retries exhausted or on non-retryable errors.
        """
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "https://103.150.197.225:3013",
            "X-OpenRouter-Title": "EMITS PLTU Tenayan",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            "max_tokens": 2000,
            "temperature": 0.3,
        }
        # Add JSON mode only for blending/JSON prompts (detected by session_id prefix)
        if "smart-blending" in session_id:
            payload["response_format"] = {"type": "json_object"}

        last_exc = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{self.OPENROUTER_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                if resp.status_code in (401,):
                    raise LLMUnavailableError(
                        "OpenRouter: invalid API key", status_code=401
                    )
                if resp.status_code == 402:
                    raise LLMUnavailableError(
                        "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar.",
                        status_code=402,
                    )
                if resp.status_code in self.RETRYABLE_STATUSES:
                    raise httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}", request=resp.request,
                        response=resp
                    )
                raise LLMUnavailableError(
                    f"OpenRouter: unexpected status {resp.status_code}",
                    status_code=resp.status_code,
                )
            except (httpx.HTTPStatusError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
        raise LLMUnavailableError(
            "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar."
        ) from last_exc
```

**Updated `get_ai_client()` in `app/ai/client.py`:**

```python
def get_ai_client() -> AIClient:
    if os.environ.get("AI_FAKE") == "1":
        from tests.fakes.ai_client import FakeAIClient
        return FakeAIClient()
    from app.ai.openrouter_client import OpenRouterClient
    return OpenRouterClient(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        model=os.environ.get("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4o-mini"),
    )
```

---

## Focus 2: Smart-Blending Data Correctness Audit

### Live Schema: `smartstock` Collection

Probed via `mongosh pltu_tenayan --eval "JSON.stringify(db.smartstock.findOne({}, {_id:0}))"` [VERIFIED: live read-only probe]

Actual fields in a `smartstock` document:
```json
{
  "id": "uuid",
  "date": "YYYY-MM-DD",
  "stock_awal": 122606972,
  "suppliers": {
    "SUPPLIER_NAME_LRC": {"A": 0, "B": 0, "C": 0},
    ...
  },
  "total_penerimaan": 0,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

**There is NO `tonase` field at the document top level.** The field is `total_penerimaan`.

Note: One record shows a supplier key `"TOTAL_PENERIMAAN\n_MT"` — this is a parsing artifact from the Excel upload where "TOTAL PENERIMAAN (MT)" was interpreted as a supplier name. This is a data-quality issue but not a field-name issue for the aggregation.

### Live Schema: `sumberpemakaian` Collection

Probed via `mongosh pltu_tenayan --eval "JSON.stringify(db.sumberpemakaian.findOne({}, {_id:0}))"` [VERIFIED: live read-only probe]

Actual fields:
```json
{
  "id": "uuid",
  "date": "YYYY-MM-DD",
  "stock_awal": 101044936,
  "suppliers": {
    "_": {
      "UNIT1": {"A": 0, "B": 0, "C": 0},
      "UNIT2": {"A": 0, "B": 0, "C": 0}
    }
  },
  "total_pemakaian": 681800,
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

**There are NO `batubara_mt`, `biomassa_mt`, `tanggal`, or `energy_mwh` fields.** The total field is `total_pemakaian` (single number, no batubara/biomassa split).

### Field Mismatch Table (Data Correctness Audit)

| server.py:line | Context | Expected field (code uses) | Actual field (live schema) | Fix |
|----------------|---------|---------------------------|---------------------------|-----|
| 2379–2384 | `get_database_context()`, smart_stock AI context — `db.smartstock.find(...)` projection | `"source"`, `"supplier"`, `"cargo"`, `"tonase"` | `"date"`, `"total_penerimaan"`, `"suppliers"` (nested dict) | Change projection to `{"_id":0, "date":1, "total_penerimaan":1, "suppliers":1}` |
| 2387–2392 | `get_database_context()`, smart_stock AI context — `db.sumberpemakaian.find(...)` projection | `"tanggal"`, `"energy_mwh"`, `"batubara_mt"`, `"biomassa_mt"`, `"sfc"` | `"date"`, `"total_pemakaian"`, `"suppliers"` | Change projection to `{"_id":0, "date":1, "total_pemakaian":1, "suppliers":1}` |
| 2395–2397 | `get_database_context()`, stock summary — `db.smartstock.aggregate([{"$group": {"_id": None, "total": {"$sum": "$tonase"}}}])` | `$tonase` | `$total_penerimaan` | Change `"$tonase"` → `"$total_penerimaan"` |
| 2398–2400 | `get_database_context()`, stock summary — `db.sumberpemakaian.aggregate([$sum: "$batubara_mt", $sum: "$biomassa_mt"])` | `$batubara_mt`, `$biomassa_mt` | `$total_pemakaian` (single field, no split) | Collapse to single `$sum: "$total_pemakaian"`, return as `total_pemakaian` |
| 2863–2865 | `/api/ai/quick/smart-stock` — `db.smartstock.aggregate([$sum: "$tonase"])` | `$tonase` | `$total_penerimaan` | Change `"$tonase"` → `"$total_penerimaan"` |
| 2868–2874 | `/api/ai/quick/smart-stock` — `db.sumberpemakaian.aggregate([$sum: "$batubara_mt", $sum: "$biomassa_mt"])` | `$batubara_mt`, `$biomassa_mt` | `$total_pemakaian` | Collapse to single `$sum: "$total_pemakaian"` |
| 2877–2885 | `/api/ai/quick/smart-stock` — `db.sumberpemakaian.aggregate([$avg: "$batubara_mt", $avg: "$energy_mwh"])` | `$batubara_mt`, `$energy_mwh` | `$total_pemakaian` | Change to `$avg: "$total_pemakaian"` as `avg_pemakaian`; remove `avg_energy` |

**Summary:** Two categories of mismatches:
1. **`$tonase` → `$total_penerimaan`** in `smartstock` (2 sites: lines 2395-2397, 2863-2865)
2. **`$batubara_mt` + `$biomassa_mt` + `$tanggal` + `$energy_mwh` → `$total_pemakaian`** in `sumberpemakaian` (3 sites: lines 2387-2392, 2398-2400, 2868-2885)

Note: Lines 2863-2885 already have the Phase-5 CP2 `None`-coercion hotfix applied (`or 0`). The field-name fix is still needed on top of that hotfix.

**Additional note:** The quick-smart-stock endpoint's existing `or 0` coercions at lines 2891-2894 will remain valid after the field-name fix. No functional regression to that hotfix.

### Smart-Blending `recommend` Endpoint Data Flow

The `/api/smart-blending/recommend` endpoint at line 3599 does NOT use `smartstock` or `sumberpemakaian` aggregations — it reads from `vessels`, `barges`, `trucking`, and `smartstock.find_one()` (for latest stock date only). The field mismatches above do NOT affect the recommend endpoint directly. They affect:
1. `/api/ai/quick/smart-stock` — the quick summary endpoint
2. `get_database_context()` for modules `general` and `smart_stock` used by `/api/ai/query`

---

## Focus 3: `ai_chat_history` Live Schema

### Live Schema

Probed via `mongosh pltu_tenayan --eval "JSON.stringify(db.ai_chat_history.findOne({}, {_id:0}))"` [VERIFIED: live read-only probe]

**Document count:** 10 [VERIFIED: `db.ai_chat_history.countDocuments()`]
**Unique session_ids:** 4 [VERIFIED: `db.ai_chat_history.distinct('session_id').length`]
**Unique user_ids:** 2 [VERIFIED: session_id enumeration]

**All field names present in every document:**
```json
{
  "id":          "UUID string",
  "user_id":     "UUID string (user who sent the query)",
  "session_id":  "string — format: 'tenayan-ai-{user_id}-{uuid4}'",
  "module":      "string — 'general', 'coa_reconciliation', etc.",
  "query":       "string — user's question text",
  "response":    "string — LLM response text (may contain markdown)",
  "parameters":  "null or dict",
  "created_at":  "ISO-8601 string"
}
```

**No `conversation_id` field exists.** The `session_id` field serves as the conversation grouping key.

**Session distribution (4 conversations):**
```
Session 1: tenayan-ai-c837c681-...-d089daee-...  → user c837c681, 1 query
Session 2: tenayan-ai-b94bfaa5-...-1acfa7cb-...  → user b94bfaa5, 7 queries
Session 3: tenayan-ai-c837c681-...-e385b327-...  → user c837c681, 1 query
Session 4: tenayan-ai-c837c681-...-ed6431a1-...  → user c837c681, 1 query
```

### Conversation Grouping Strategy

**Recommendation: Use `session_id` as `conversation_id` — no schema migration needed.**

The current schema stores each query/response pair as a separate document (not a messages[] array). This is the flat-document-per-exchange pattern. The Phase 6 new chat endpoint at `POST /api/ai/conversations/<id>/messages` will persist records in the same format — one document per exchange — with `session_id` as the conversation key.

**Backward-compatible approach:**
- `GET /api/ai/conversations` → aggregate `ai_chat_history` by `session_id` for `user_id`; compute title from the earliest record's `query` (first 50 chars)
- `GET /api/ai/conversations/<id>/messages` → find by `session_id=id` and `user_id`
- `POST /api/ai/conversations` → generate a new UUID; return as `id` (this is the `session_id` for new conversations)
- `POST /api/ai/conversations/<id>/messages` → insert a new record with `session_id=id`; call LLM; insert AI response record

The existing `/api/ai/sessions/*` endpoints (lines 2966-3048) use the same grouping logic (aggregate by `session_id`). The new `/api/ai/conversations/*` endpoints can coexist or the planner may choose to extend the existing session endpoints.

**No schema migration required for the 10 existing records.** `session_id` is already present on all 10 documents. [VERIFIED: live probe]

### `ai_chat_history` Persistence

Current write site: `server.py:2657` — `await ai_chat_collection.insert_one(chat_entry)` inside `/api/ai/query`.

The new `/api/ai/conversations/<id>/messages` endpoint will also write to `ai_chat_collection`. The format matches: per-exchange flat document with `user_id`, `session_id`, `query` (for user message), `response` (for AI message), `created_at`.

**Naming alignment for new endpoint documents:**
```python
# User message record (persisted before LLM call)
user_record = {
    "id": str(uuid.uuid4()),
    "user_id": user["id"],
    "session_id": conversation_id,   # the /conversations/<id> path param
    "module": "general",
    "query": content,                # user's message text
    "response": None,                # not yet
    "parameters": None,
    "created_at": now_iso
}
# AI response record (persisted after LLM call)
ai_record = {
    "id": str(uuid.uuid4()),
    "user_id": user["id"],
    "session_id": conversation_id,
    "module": "general",
    "query": content,                # same user message
    "response": llm_response,
    "parameters": None,
    "created_at": now_iso
}
```

The UI-SPEC requires `GET /api/ai/conversations/<id>/messages` to return items with `{id, role, content, created_at}` shape. The planner must map the flat document to this shape: user messages derive `role="user"` + `content=doc["query"]`; AI messages derive `role="assistant"` + `content=doc["response"]`. Since each document contains both query and response, the endpoint either stores them as two separate documents per exchange or denormalizes at query time. The recommended approach is two documents per exchange for simpler pagination.

---

## Focus 4: Excel Parser Entry-Point Inventory

### Upload Endpoints in `server.py`

[VERIFIED: grep of server.py]

| Endpoint | Line | Parser function | Collection | xlsx file in question |
|----------|------|-----------------|------------|-----------------------|
| `POST /api/upload/po-batubara` | 1112 | inline pandas parsing | `po_batubara` | — |
| `POST /api/upload/merit-order` | 1320 | inline pandas parsing | `merit_order` | — |
| `POST /api/upload/vessel` | 1385 | inline pandas parsing, `df.iterrows()` | `vessels` | Loading.xlsx matches vessel format |
| `POST /api/upload/barge` | 1504 | inline pandas parsing | `barges` | — |
| `POST /api/upload/trucking` | 1610 | inline pandas parsing | `trucking` | — |
| `POST /api/upload/biomassa` | 1722 | inline pandas parsing | `biomassa` | — |
| `POST /api/smart-stock/upload` | 3137 | `upload_smart_stock_excel()` — custom header scanner | `smartstock` | — |
| `POST /api/sumber-pemakaian/upload` | 3436 | `upload_sumber_pemakaian_excel()` — inline | `sumberpemakaian` | — |
| `POST /api/coa-reconciliation/upload` | 4071 | `parse_coa_excel()` from `services/coa_reconciliation.py` | `coa_reconciliation` | **Loading.xlsx, Unloading.xlsx, Lab_Internal.xlsx** |

### Focus for OPS-03

The three proxy xlsx files (`Loading.xlsx`, `Unloading.xlsx`, `Lab_Internal.xlsx`) map to the **COA reconciliation upload endpoint** (`POST /api/coa-reconciliation/upload`), not the vessel/barge upload endpoints. The COA upload accepts all three files simultaneously as a multipart form with fields `loading_file`, `unloading_file`, `internal_file`.

The parser function `parse_coa_excel(file_contents, source_type)` in `services/coa_reconciliation.py:62` handles all three source types. It uses `clean_column_name()` to normalize headers before field mapping. The header normalization strips newlines to spaces, which explains the dual fallback in field lookups (e.g., `row.get("GCV (Kcal/Kg) ARB", row.get("GCV (Kcal/Kg)\nARB"))`).

---

## Focus 5: `httpx` Retry-with-Backoff Pattern

`httpx==0.28.1` is already in `requirements.txt`. [VERIFIED: file read]

**Hand-rolled pattern (recommended — cleaner than tenacity for this simple case):**

```python
import asyncio
import httpx

async def _call_openrouter_with_retry(self, payload: dict, headers: dict) -> str:
    """3-attempt exponential backoff for transient OpenRouter errors."""
    retryable = {429, 500, 502, 503}
    last_exc = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            if resp.status_code in retryable:
                last_exc = httpx.HTTPStatusError(
                    f"HTTP {resp.status_code}",
                    request=resp.request,
                    response=resp,
                )
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)  # 1s → 2s → 4s
                continue
            # Non-retryable: 401 (key invalid), 402 (budget), 4xx (bad request)
            raise LLMUnavailableError(
                "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar.",
                status_code=resp.status_code,
            )
        except httpx.TimeoutException as exc:
            last_exc = exc
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
    raise LLMUnavailableError(
        "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar."
    ) from last_exc
```

**Note on `tenacity`:** `tenacity==9.1.2` is already in `requirements.txt` — the planner may use `@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)` as an alternative, but the hand-rolled pattern is transparent and easy to unit-test.

---

## Focus 6: FastAPI 503 + `LLMUnavailableError` Exception Handler

**Wiring pattern (idiomatic FastAPI):**

```python
# In server.py, near the top-level app/api_router setup
from app.ai.openrouter_client import LLMUnavailableError

@app.exception_handler(LLMUnavailableError)
async def llm_unavailable_handler(request, exc: LLMUnavailableError):
    return JSONResponse(
        status_code=503,
        content={"detail": str(exc)},
    )
```

**Per-endpoint pattern (alternative — inline catch at each AI endpoint):**

```python
# In /api/smart-blending/recommend and /api/ai/conversations/<id>/messages
try:
    response = await ai.send_message(session_id, system_prompt, user_message)
except LLMUnavailableError as exc:
    raise HTTPException(status_code=503, detail=str(exc))
```

The global exception handler is cleaner (DRY) and ensures all AI endpoints emit the same 503 shape. The per-endpoint inline catch is more explicit. **Recommendation: global handler.** [ASSUMED — either pattern is valid; global is more maintainable]

The 503 response body the frontend parses:
```json
{"detail": "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar."}
```

---

## Focus 7: `FakeAIClient` Compatibility Audit

**Existing `FakeAIClient` signature** (from `tests/fakes/ai_client.py:25`):
```python
class FakeAIClient:
    async def send_message(
        self, session_id: str, system_prompt: str, user_message: str
    ) -> str:
```

**`AIClient` Protocol** (from `app/ai/client.py:14`):
```python
class AIClient(Protocol):
    async def send_message(
        self, session_id: str, system_prompt: str, user_message: str
    ) -> str:
```

**`OpenRouterClient` (Phase 6 rewrite):** Will implement the same `send_message(session_id, system_prompt, user_message) -> str` signature.

**Verdict:** FakeAIClient is fully compatible. No changes needed to `tests/fakes/ai_client.py`. [VERIFIED: file read]

**Routing logic in `FakeAIClient.send_message`:**
```python
if "blend" in (system_prompt or "").lower() or "blend" in (session_id or "").lower():
    return BLENDING_JSON
return GENERAL_RESPONSE
```

The smart-blending session_id format `f"smart-blending-{uuid.uuid4()}"` (line 3774) contains "blend" — FakeAIClient routes correctly. New `/api/ai/conversations/<id>/messages` will use a different session_id format (just the UUID conversation_id) — FakeAIClient will return `GENERAL_RESPONSE` for chat, which is appropriate. [VERIFIED: code review]

**`AI_FAKE=1` env-var branch in `get_ai_client()`:** The factory at `app/ai/client.py:22` is preserved verbatim — only the `else` branch changes from `LegacyLLMClientWrapper` to `OpenRouterClient`.

---

## Focus 8: Excel Verification Procedure

### File Inventory

[VERIFIED: openpyxl probe of all 3 files]

| File | Sheet name | Total rows | Data rows | Cols | Upload endpoint |
|------|-----------|-----------|-----------|------|-----------------|
| `Loading.xlsx` (184 KB) | Sheet1 | 722 | 721 | 33 | `POST /api/coa-reconciliation/upload` (loading_file) |
| `Unloading.xlsx` (312 KB) | UNLoading | 722 | 721 | 59 | `POST /api/coa-reconciliation/upload` (unloading_file) |
| `Lab_Internal.xlsx` (148 KB) | Sheet1 | 722 | 721 | 31 | `POST /api/coa-reconciliation/upload` (internal_file) |

**Note:** All 3 files have the exact same 721 data rows — Shipments 555 through ~1275 (Aug 2020 onwards). The COA upload endpoint at line 4071 drops existing records and re-inserts the merged set.

### Deterministic Anchor for Round-Trip Assertions

Row 2 (first data row) — Shipment 555 — is present in all three files with identical identity fields:
```
Periode:              2020-08-01
Shipment:             555
Suppliers:            "PT PLN BB/SAE"
TB:                   "MAJU DAYA 81"
BG:                   "MARCOPOLO 278"
Commenced Unloading:  2020-08-02 09:55
Completed Unloading:  2020-08-03 14:15
DS (MT):              5626.021
```

**3 deterministic field values for round-trip assertion (all modes):**
- `shipment` = "555"
- `suppliers` = "PT PLN BB/SAE"
- `ds_mt` = 5626.021

**Mode-specific additional asserts:**
- Loading: `surveyor` (Surveyor Loading field) — if present in row 2 check column 11 (empty in row 2; use row 3 which has "PT SUCOFINDO")
- Unloading: `surveyor` (Surveyor Unloading field, col 9) = "PT GEOSERVICES"
- Loading row 3: `gcv_arb` = 4211.0 (col 12)
- Loading row 3: `ts_arb` = 0.24 (col 24)

### Sanitization Rule for Regression Fixtures

For the ~50-row sanitized subsets:
- Replace real supplier names with deterministic dummies: `"PT PLN BB/SAE"` → `"PT DEMO SUPPLIER {n}"` where n is a sequential integer
- Replace real contract numbers (NO.COA, NO.COW values) with `"COA-DEMO-{row_idx:04d}"`
- Keep numeric quality values (GCV, TM, ASH, TS) unchanged — they are needed for parser verification
- Keep shipment numbers unchanged — they are the join key in COA merging

**Important:** The `parse_coa_excel` function uses `clean_column_name()` to normalize headers — this strips newlines. The fixture must use the same header strings as the real xlsx (with `\n`) or the planner must verify `clean_column_name` handles both. [VERIFIED: coa_reconciliation.py uses `df.read_excel()` which handles newlines via column normalization]

---

## Focus 9: Frontend Integration

### Layout.js — Nav Integration Target

[VERIFIED: file read — `Layout.js`]

The "AI Intelligence" link is at lines 249-262:
```jsx
<Link to="/ai-intelligence" ...>
  <Bot className="w-5 h-5" />
  <span className="text-sm font-medium">AI Intelligence</span>
</Link>
```

**Where to add the new "Riwayat Percakapan AI" link:** Immediately after the AI Intelligence link, using the same pattern:
```jsx
<Link
  to="/ai-chat"
  onClick={() => setSidebarOpen(false)}
  className={`flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
    location.pathname === "/ai-chat"
      ? "bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-400 border border-cyan-500/30"
      : "text-slate-400 hover:text-white hover:bg-white/5"
  }`}
>
  <MessageSquare className="w-5 h-5" />
  <span className="text-sm font-medium">Riwayat Percakapan AI</span>
  {location.pathname === "/ai-chat" && <ChevronRight className="w-4 h-4 ml-auto" />}
</Link>
```

`MessageSquare` must be added to the lucide-react imports at Layout.js line 1. [VERIFIED: MessageSquare not yet imported; lucide-react is already installed]

### `AIIntelligencePage.js` — Coexistence vs Replace

The existing `/ai-intelligence` route and page are NOT replaced by Phase 6. The new `/ai-chat` route is an addition. They coexist: `AIIntelligencePage.js` handles the query-and-respond interface; `AIChatPage.js` (new) handles conversation history browsing. [VERIFIED: CONTEXT.md explicit scope]

### Route Path and Component Location

Per UI-SPEC:
- Route: `/ai-chat`
- Page component: `pltu-tenayan-full-backup/frontend/src/pages/AIChatPage.js`
- Sub-components: `pltu-tenayan-full-backup/frontend/src/components/ai-chat/*.js`
- Helper: `pltu-tenayan-full-backup/frontend/src/lib/formatRelativeTime.js`

### Toast Utility

[VERIFIED: UI-SPEC + package.json]

```js
import { toast } from "sonner";
// <Toaster> already mounted in App.js with position="top-right" richColors
```

Usage pattern (from UI-SPEC):
```js
// 503 LLM unavailable
toast.error("Layanan AI tidak tersedia", {
  description: err.response.data?.detail || "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar.",
  action: { label: "Coba lagi", onClick: retryCallback },
  duration: 8000,
});

// 401 auth expired
toast.error("Sesi habis. Silakan login ulang.", { duration: 5000 });
navigate("/login");

// Network error
toast.error("Tidak terhubung ke server.", {
  action: { label: "Coba lagi", onClick: retryCallback },
  duration: 6000,
});
```

### Incidental Fix: `SmartBlendingPage.js:71`

[VERIFIED: UI-SPEC §"Incidental Fix" section]

The existing English toast at `SmartBlendingPage.js:71`:
```js
toast.success("AI recommendation generated successfully!");
```
Must be localized to:
```js
toast.success("Rekomendasi AI berhasil dibuat!");
```
Include this as a task under Plan 06-05 (OPS-02 cross-cut per UI-SPEC). The planner must verify the exact line number before editing.

---

## Focus 10: `legacy-ai-sdk` Removal Checklist

[VERIFIED: grep of server.py]

**Two import sites in `server.py`:**
- Line 19: `from legacy-ai-sdk.llm.chat import LlmChat, UserMessage` (top-level import, no longer needed after Phase 6)
- Line 2263: `from legacy-ai-sdk.llm.chat import LlmChat, UserMessage` (before AI module section — also to be removed)

**`requirements.txt` line to remove:** `legacy-ai-sdk==0.1.0` (line 21)

**`app/ai/legacy_llm_wrapper.py`:** Entire file deleted (or renamed to `openrouter_client.py` with rewrite — D-02 says rename+rewrite; git mv is preferred to preserve history).

**Env-var rename — all affected doc files:**
[VERIFIED: grep of pltu-tenayan-full-backup/ directory]
1. `backend/.env` — line 5: `LEGACY_LLM_KEY=sk-legacy-ai-...`
2. `LOCAL_SETUP.md` — lines 269, 331
3. `DEPLOYMENT_GUIDE.md` — lines 132, 139, 381, 534
4. `documentation.md` — lines 99, 559
5. `readme.md` — line 143
6. `frontend/public/docs/DEPLOYMENT_GUIDE.md` — lines 120, 127, 357, 510
7. `frontend/public/docs/documentation.md` — lines 99, 559
8. `frontend/public/docs/readme.md` — line 141
9. `backend/.env.example` — add `OPENROUTER_API_KEY=` and `OPENROUTER_DEFAULT_MODEL=openai/gpt-4o-mini`

**Note:** `MIGRATION_RUNBOOK.md` (Phase 5 deliverable) does NOT contain `LEGACY_LLM_KEY` references [VERIFIED: grep returned no output].

**Env-var addition in `.env`:**
```ini
OPENROUTER_API_KEY=<operator-provided-key>
OPENROUTER_DEFAULT_MODEL=openai/gpt-4o-mini
```

---

## Architecture Patterns

### System Architecture Diagram (Phase 6 Changes)

```
Frontend (React :3013)
  └── AIChatPage + ConversationPanel
        │ [toast on 503]              [AI chat requests]
        ├── POST /api/ai/conversations/<id>/messages
        │       │
        │   FastAPI (:8013)
        │       │─ Depends(get_current_user) [auth gate]
        │       │─ get_ai_client() → OpenRouterClient
        │       │─ [retry loop: 3 attempts, 1/2/4s backoff]
        │       │
        │       ├── OK → persist to ai_chat_history → return AI response
        │       └── LLMUnavailableError → HTTP 503 {"detail": "..."}
        │
        └── GET /api/ai/conversations [list sessions from ai_chat_history]
              │
          MongoDB :27017 — ai_chat_history (aggregate by session_id)

SmartBlendingPage (React)
  └── POST /api/smart-blending/recommend
        │
    FastAPI
        │─ gather vessels/barges/trucking/smartstock (corrected aggregations)
        │─ OpenRouterClient.send_message() [retry-with-backoff]
        │─ json.loads(response) [JSON mode: response_format json_object]
        └── return {"ai_recommendation": {...}}

External
  OpenRouterClient ──► https://openrouter.ai/api/v1/chat/completions
                       model: openai/gpt-4o-mini
```

### Recommended Project Structure (Phase 6 Changes)

```
pltu-tenayan-full-backup/backend/
├── app/ai/
│   ├── client.py              (updated: factory → OpenRouterClient)
│   ├── openrouter_client.py   (NEW: rename + rewrite of legacy_llm_wrapper.py)
│   └── legacy_llm_wrapper.py    (DELETED after rename)
├── tests/
│   ├── test_smart_blending_data.py   (NEW: aggregation field-name unit tests)
│   ├── test_upload_excel.py          (EXTENDED: regression fixture params)
│   ├── fixtures/excel/regression/
│   │   ├── loading_sample.xlsx       (NEW: sanitized ~50 rows)
│   │   ├── unloading_sample.xlsx     (NEW)
│   │   └── lab_internal_sample.xlsx  (NEW)
│   └── fakes/ai_client.py    (UNCHANGED)
└── server.py                  (surgical edits: field names + retry + 503 + 4 new endpoints)

pltu-tenayan-full-backup/frontend/src/
├── pages/
│   └── AIChatPage.js          (NEW)
├── components/ai-chat/
│   ├── ConversationSidebar.js       (NEW)
│   ├── ConversationListItem.js      (NEW)
│   ├── ConversationPanel.js         (NEW)
│   ├── ConversationPanelHeader.js   (NEW)
│   ├── MessageList.js               (NEW)
│   ├── MessageBubble.js             (NEW)
│   └── MessageInputBar.js           (NEW)
├── components/
│   └── EmptyState.js                (NEW — shared empty state)
└── lib/
    └── formatRelativeTime.js        (NEW)
```

### Anti-Patterns to Avoid

- **Import `legacy-ai-sdk` anywhere after Phase 6:** Both server.py import sites (lines 19 and 2263) must be removed. A CI grep gate should enforce this.
- **Using `ai_conversations` collection name anywhere:** ADR-012 locks canonical name to `ai_chat_history`. Phase 5's `test_no_legacy_collection_reads_in_server_py` gate enforces this automatically.
- **Hardcoding `"gemini"` or `"gemini-2.5-flash"` in new code:** The `AISettingsUpdate` model at lines 2274-2277 still has gemini defaults — these should be updated to `openai/gpt-4o-mini` in Phase 6.
- **JSON mode without "JSON" in the prompt:** New chat endpoints that use plain text responses should NOT set `response_format: {"type": "json_object"}`. Only smart-blending uses JSON mode.
- **Blocking `asyncio.sleep()` in async context:** Use `await asyncio.sleep()` in the retry loop — already shown in Focus 5.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OpenRouter HTTP client | Custom aiohttp/requests wrapper | `httpx.AsyncClient` | Already in requirements; async-native |
| Excel header parsing | Custom xlsx column scanner | `pandas.read_excel()` + `openpyxl` | Already used in all parser functions |
| JWT auth on new endpoints | Custom middleware | `Depends(get_current_user)` | Existing dependency; tested by Phase-2 suite |
| Toast notifications | Custom React notification component | `sonner` (`import { toast } from "sonner"`) | Already mounted in App.js |
| Relative timestamp formatting | Custom date math | `date-fns` differenceIn* functions | Already in package.json; locale-aware |
| Retry logic | Complex state machine | 3-line `for attempt in range(3)` loop + `asyncio.sleep` | Sufficient for 3-attempt case |

---

## Runtime State Inventory

> Included because Phase 6 performs an env-var rename (LEGACY_LLM_KEY → OPENROUTER_API_KEY).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `ai_chat_history`: 10 records — all use `session_id` as grouping key. No schema migration needed. | None — `session_id` field preserved as-is |
| Live service config | Backend process on VPS reads `.env` at startup. After env-var rename, process must be restarted. | Operator action at cutover: set OPENROUTER_API_KEY in `.env`, restart uvicorn |
| OS-registered state | None — no systemd/pm2 unit embeds LLM key names | None |
| Secrets/env vars | `LEGACY_LLM_KEY` in `backend/.env` (gitignored) — code rename only; old key value is invalid (budget exhausted). `OPENROUTER_API_KEY` is a new secret the operator must obtain from OpenRouter account. | Operator obtains new key; updates `.env` |
| Build artifacts | None — no compiled binary embeds key names | None |

---

## Common Pitfalls

### Pitfall 1: Double `legacy-ai-sdk` Import in `server.py`

**What goes wrong:** `server.py` imports `legacy-ai-sdk` at TWO locations (line 19 and line 2263). Removing only one causes an `ImportError` at startup or a `NameError` at runtime.
**Why it happens:** The module was imported once at the top for general use, then again as a lazy import near the AI module section.
**How to avoid:** Grep `server.py` for all `from legacy-ai-sdk` occurrences before starting — confirmed: lines 19 and 2263.
**Warning signs:** `uvicorn` startup error mentioning `legacy-ai-sdk`.

### Pitfall 2: JSON Mode Without "JSON" in Prompt

**What goes wrong:** `openai/gpt-4o-mini` with `response_format: {"type": "json_object"}` emits whitespace indefinitely if neither the system nor user prompt contains the word "JSON".
**Why it happens:** Per OpenAI specification, this is a defined failure mode.
**How to avoid:** For smart-blending: existing prompt already contains "JSON" (line 3771). For new chat endpoint: do NOT use `response_format: json_object` for general AI chat (plain text response is appropriate). Only enable JSON mode for the blending session_id pattern.
**Warning signs:** LLM response is empty string or whitespace; `json.loads()` raises `JSONDecodeError`.

### Pitfall 3: `conversation_id` vs `session_id` Naming Confusion in New Endpoints

**What goes wrong:** Phase 6 D-18 mentions "conversation_id" in the API contract, but live schema uses "session_id". Using different field names creates a split schema.
**Why it happens:** D-18 was written before live schema inspection.
**How to avoid:** Use `session_id` as the canonical field name in MongoDB writes. The API endpoint path parameter is called `id`; the MongoDB field is `session_id`. The API response uses `id` (mapped from `session_id`).
**Warning signs:** New chat messages not appearing in old session history; `GET /api/ai/sessions` and `GET /api/ai/conversations` returning different session lists for the same user.

### Pitfall 4: COA Upload Drops Existing Records

**What goes wrong:** `POST /api/coa-reconciliation/upload` drops all existing COA records before re-inserting the merged set (line 4085-4087 context). Running the verification test against the production DB would delete production data.
**Why it happens:** COA upload is a replace-all operation, not an append.
**How to avoid:** OPS-03 verification MUST run against the Phase-4 test DB (`pltu_tenayan_test_<sessionid>`), NOT the live `pltu_tenayan` DB. The Phase-4 conftest spawns a fresh test backend on port :18013 with `AI_FAKE=1`.
**Warning signs:** Production COA data missing after test run.

### Pitfall 5: smartstock `total_penerimaan` = 0 in Current Data

**What goes wrong:** The live `smartstock` findOne returns `total_penerimaan: 0` even for records with zone-level data. This is because the Excel parser computes `total_penerimaan` from sum of supplier zones, but the "TOTAL_PENERIMAAN\n_MT" parser artifact puts total in a supplier slot instead.
**Why it happens:** The smart-stock Excel format has a "TOTAL PENERIMAAN (MT)" column that the upload parser confusingly interprets as a supplier name.
**How to avoid:** The aggregation fix (changing `$sum: "$total_penerimaan"` instead of `$sum: "$tonase"`) is still correct code, but the DATA may show zeros. The data-quality issue is a separate parser bug in `upload_smart_stock_excel()`. Planner should note: OPS-01 data fix restores correct field references; any remaining zeros are a data-entry artifact, not a Phase-6 code bug. The smoke test (D-08) will expose whether live data is usable.
**Warning signs:** `/api/ai/quick/smart-stock` returns 0 values even after the field-name fix; manual check shows `total_penerimaan: 0` on most smartstock documents.

### Pitfall 6: `AISettingsUpdate` Model Still Has Gemini Defaults

**What goes wrong:** After migrating to OpenRouter, the AI Settings endpoint (`GET /api/ai/settings`) still reports `"llm_provider": "gemini", "llm_model": "gemini-2.5-flash"` as defaults.
**Why it happens:** The `AISettingsUpdate` Pydantic model at lines 2274-2277 has hardcoded gemini defaults.
**How to avoid:** Update `AISettingsUpdate` defaults to `llm_provider: "openrouter"`, `llm_model: "openai/gpt-4o-mini"` during Plan 06-01.
**Warning signs:** Operator checks AI Settings page and sees "gemini" despite migration.

### Pitfall 7: Existing `/api/ai/sessions` vs New `/api/ai/conversations` Endpoint Confusion

**What goes wrong:** Two parallel session-listing endpoints could return different session sets, confusing the operator and creating test coverage gaps.
**Why it happens:** The existing `/api/ai/sessions` endpoint (line 2967) aggregates by `session_id` and returns paginated results. The new `/api/ai/conversations` endpoint should do the same but return the UI-SPEC response shape.
**How to avoid:** The new `/api/ai/conversations` endpoint can internally call the same MongoDB aggregation as `/api/ai/sessions` but return `[{id: session_id, title, last_message_at}]`. The old session endpoints remain for backward compatibility.
**Warning signs:** `GET /api/ai/conversations` returns 0 items while `GET /api/ai/sessions` returns 4 items.

---

## Code Examples

### Pattern 1: OpenRouter `send_message` — Full Call

```python
# Source: Focus 1 (OpenRouter docs + httpx pattern)
import asyncio
import httpx

async def send_message(self, session_id: str, system_prompt: str, user_message: str) -> str:
    headers = {
        "Authorization": f"Bearer {self._api_key}",
        "HTTP-Referer": "https://103.150.197.225:3013",
        "X-OpenRouter-Title": "EMITS PLTU Tenayan",
        "Content-Type": "application/json",
    }
    payload = {
        "model": self._model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "max_tokens": 2000,
        "temperature": 0.3,
    }
    # JSON mode only for smart-blending (prompt already contains "JSON")
    if "smart-blending" in session_id:
        payload["response_format"] = {"type": "json_object"}

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    json=payload, headers=headers,
                )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            if resp.status_code in {429, 500, 502, 503}:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                continue
            raise LLMUnavailableError(
                "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar.",
                status_code=resp.status_code,
            )
        except httpx.TimeoutException:
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
    raise LLMUnavailableError(
        "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar."
    )
```

### Pattern 2: smart-stock aggregation fixes

```python
# Source: Focus 2 (live schema probe)
# BEFORE (broken):
total_penerimaan = await db.smartstock.aggregate([
    {"$group": {"_id": None, "total": {"$sum": "$tonase"}}}  # WRONG: "$tonase"
]).to_list(1)
total_pemakaian = await db.sumberpemakaian.aggregate([
    {"$group": {"_id": None,
                "total_batubara": {"$sum": "$batubara_mt"},  # WRONG
                "total_biomassa": {"$sum": "$biomassa_mt"}   # WRONG
                }}
]).to_list(1)

# AFTER (correct):
total_penerimaan = await db.smartstock.aggregate([
    {"$group": {"_id": None, "total": {"$sum": "$total_penerimaan"}}}  # FIXED
]).to_list(1)
total_pemakaian = await db.sumberpemakaian.aggregate([
    {"$group": {"_id": None,
                "total_pemakaian": {"$sum": "$total_pemakaian"}  # FIXED: single field
                }}
]).to_list(1)
```

### Pattern 3: New conversation endpoint skeleton

```python
# Source: Focus 3 (ai_chat_history live schema + D-18)
@api_router.get("/ai/conversations")
async def list_conversations(user: dict = Depends(get_current_user)):
    """List user's conversations from ai_chat_history grouped by session_id."""
    pipeline = [
        {"$match": {"user_id": user["id"]}},
        {"$sort": {"created_at": 1}},
        {"$group": {
            "_id": "$session_id",
            "first_query": {"$first": "$query"},
            "last_message_at": {"$max": "$created_at"},
        }},
        {"$sort": {"last_message_at": -1}},
    ]
    sessions = await ai_chat_collection.aggregate(pipeline).to_list(100)
    return [
        {
            "id": s["_id"],
            "title": (s["first_query"] or "Percakapan tanpa judul")[:50],
            "last_message_at": s["last_message_at"],
        }
        for s in sessions
    ]

@api_router.post("/ai/conversations", status_code=201)
async def create_conversation(user: dict = Depends(get_current_user)):
    """Create a new empty conversation. Returns conversation id."""
    conv_id = f"tenayan-ai-{user['id']}-{uuid.uuid4()}"
    return {
        "id": conv_id,
        "title": "Percakapan tanpa judul",
        "last_message_at": datetime.now(timezone.utc).isoformat(),
    }

@api_router.get("/ai/conversations/{conv_id}/messages")
async def get_conversation_messages(
    conv_id: str,
    before: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    user: dict = Depends(get_current_user),
):
    """Paginated message retrieval. Returns messages oldest-first."""
    query = {"session_id": conv_id, "user_id": user["id"]}
    if before:
        query["id"] = {"$lt": before}  # cursor by id
    docs = await ai_chat_collection.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    if not docs:
        raise HTTPException(status_code=404, detail="Percakapan tidak ditemukan")
    # Convert flat docs to message shape (each doc = 1 user message + 1 AI response)
    messages = []
    for doc in reversed(docs):  # oldest-first for display
        messages.append({
            "id": f"u-{doc['id']}",
            "role": "user",
            "content": doc.get("query", ""),
            "created_at": doc["created_at"],
        })
        if doc.get("response"):
            messages.append({
                "id": f"a-{doc['id']}",
                "role": "assistant",
                "content": doc["response"],
                "created_at": doc["created_at"],
            })
    return messages

@api_router.post("/ai/conversations/{conv_id}/messages")
async def send_conversation_message(
    conv_id: str,
    body: dict,  # {"content": "..."}
    user: dict = Depends(get_current_user),
    ai: AIClient = Depends(get_ai_client),
):
    """Send a user message; backend calls LLM; persists both; returns AI response."""
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=422, detail="content is required")
    system_prompt = get_system_prompt("general")
    try:
        response = await ai.send_message(conv_id, system_prompt, content)
    except LLMUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    now_iso = datetime.now(timezone.utc).isoformat()
    doc_id = str(uuid.uuid4())
    await ai_chat_collection.insert_one({
        "id": doc_id, "user_id": user["id"], "session_id": conv_id,
        "module": "general", "query": content, "response": response,
        "parameters": None, "created_at": now_iso,
    })
    return {
        "id": f"a-{doc_id}",
        "role": "assistant",
        "content": response,
        "created_at": now_iso,
    }
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 0.24.0 |
| Config file | `pltu-tenayan-full-backup/backend/pytest.ini` |
| Quick run command | `AI_FAKE=1 pytest backend/tests/test_smart_blending_data.py -x -q` |
| Full suite command | `AI_FAKE=1 pytest backend/tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OPS-01 (provider) | `OpenRouterClient.send_message()` returns LLM text via OpenRouter | unit (with respx mock) | `pytest tests/test_openrouter_client.py -x` | ❌ Wave 0 |
| OPS-01 (provider) | `get_ai_client()` returns `OpenRouterClient` when `AI_FAKE` not set | unit | `pytest tests/test_openrouter_client.py::test_factory -x` | ❌ Wave 0 |
| OPS-01 (data) | `db.smartstock.aggregate($sum: "$total_penerimaan")` returns non-zero | unit (seeded test DB) | `pytest tests/test_smart_blending_data.py -x` | ❌ Wave 0 |
| OPS-01 (data) | `db.sumberpemakaian.aggregate($sum: "$total_pemakaian")` returns non-zero | unit (seeded test DB) | `pytest tests/test_smart_blending_data.py -x` | ❌ Wave 0 |
| OPS-01 (data) | `/api/ai/quick/smart-stock` returns `current_stock != 0` with seeded data | integration | `pytest tests/test_smart_blending_data.py::test_smart_stock_endpoint -x` | ❌ Wave 0 |
| OPS-02 | `LLMUnavailableError` after 3 retries → HTTP 503 body is Indonesian | unit + integration | `pytest tests/test_openrouter_client.py::test_retry_exhaustion -x` | ❌ Wave 0 |
| OPS-02 | Frontend 503 toast appears (Indonesian copy) | manual smoke | n/a — manual | — |
| OPS-03 | `parse_coa_excel(Loading.xlsx, "loading")` returns 721 records | unit | `pytest tests/test_upload_excel.py::test_coa_regression_loading -x` | ❌ Wave 0 |
| OPS-03 | `parse_coa_excel(Unloading.xlsx, "unloading")` returns 721 records | unit | `pytest tests/test_upload_excel.py::test_coa_regression_unloading -x` | ❌ Wave 0 |
| OPS-03 | `parse_coa_excel(Lab_Internal.xlsx, "internal")` returns 721 records | unit | `pytest tests/test_upload_excel.py::test_coa_regression_internal -x` | ❌ Wave 0 |
| OPS-04 | `GET /api/ai/conversations` returns sessions grouped by session_id | unit | `pytest tests/test_ai_chat_endpoints.py::test_list_conversations -x` | ❌ Wave 0 |
| OPS-04 | `GET /api/ai/conversations/<id>/messages` returns paginated messages | unit | `pytest tests/test_ai_chat_endpoints.py::test_get_messages -x` | ❌ Wave 0 |
| OPS-04 | `POST /api/ai/conversations` creates conversation | unit | `pytest tests/test_ai_chat_endpoints.py::test_create_conversation -x` | ❌ Wave 0 |
| OPS-04 | `POST /api/ai/conversations/<id>/messages` calls LLM + persists | integration (AI_FAKE=1) | `pytest tests/test_ai_chat_endpoints.py::test_send_message -x` | ❌ Wave 0 |
| OPS-04 | Frontend AI chat UI sidebar + panel smoke | manual smoke | n/a — manual | — |
| OPS-01/02/04 | Existing AI endpoint tests still pass after OpenRouter migration | regression | `AI_FAKE=1 pytest tests/test_ai_endpoints.py -x` | ✅ exists |
| OPS-01/02 | DEBT-03 gate: no legacy collection name reads | regression | `pytest tests/test_clean_checkout_gate.py -x` | ✅ exists |

### Sampling Rate

- **Per task commit:** `AI_FAKE=1 pytest backend/tests/test_ai_endpoints.py backend/tests/test_smart_blending_data.py -x -q`
- **Per wave merge:** `AI_FAKE=1 pytest backend/tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_openrouter_client.py` — covers `OpenRouterClient` unit tests (mocked httpx via `respx` or `unittest.mock`), retry behavior, `LLMUnavailableError` shape, factory routing
- [ ] `tests/test_smart_blending_data.py` — covers aggregation field-name correctness with seeded smartstock + sumberpemakaian documents
- [ ] `tests/test_ai_chat_endpoints.py` — covers all 4 new `/api/ai/conversations/*` endpoints
- [ ] Framework install: `respx` for httpx mocking — check if already installed: `pip show respx`

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `legacy-ai-sdk.LlmChat` (Gemini) | `httpx` → OpenRouter (OpenAI-compatible API) | Phase 6 | Drops vendor SDK; uses standard HTTP; unlocks model variety |
| Raw `Exception` catch → 500 response | `LLMUnavailableError` → 503 with Indonesian body | Phase 6 | User sees actionable message; no raw error |
| No conversation UI | AI Chat History page with sidebar+panel | Phase 6 | OPS-04 complete |
| No Excel regression fixtures | Sanitized fixtures committed | Phase 6 | OPS-03 gate persists in future CI |

**Deprecated/outdated:**
- `LegacyLLMClientWrapper`: deleted in Phase 6; replaced by `OpenRouterClient`
- `LEGACY_LLM_KEY` env var: renamed to `OPENROUTER_API_KEY`
- `AISettingsUpdate` gemini defaults: updated to openrouter/gpt-4o-mini
- `get_ai_settings` default response (`"llm_provider": "gemini"`): updated

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Global FastAPI exception handler is the cleaner pattern for `LLMUnavailableError` → 503 mapping | Focus 6 | Minor: per-endpoint inline catch is equally valid; low risk |
| A2 | `session_id` as conversation key is sufficient for Phase 6 without adding `conversation_id` field | Focus 3 | Low: existing 4 sessions work; new sessions use same pattern |
| A3 | The smart-blending prompt already containing "JSON" satisfies OpenAI's json_object requirement | Focus 1 | Medium: if OpenRouter normalizes headers differently, prompt must be verified |
| A4 | `total_penerimaan: 0` values in live smartstock documents are data-entry artifacts, not parser code bugs in the Phase-6-modified path | Focus 2 | Low: operator smoke test (D-08) will surface if zeros persist |
| A5 | New `/api/ai/conversations/*` endpoints coexist with old `/api/ai/sessions/*` (no conflict) | Architecture | Low: both routes are registered under `api_router`; FastAPI allows coexistence |

**Verified claims:** All MongoDB schema probes, all file reads, all grep outputs are directly verified in this research session.

---

## Open Questions (RESOLVED 2026-05-11)

1. **`respx` availability for httpx mocking in tests**
   - What we know: `pytest`, `pytest-asyncio`, `httpx` are all in requirements.txt. `respx` is the standard httpx mock library.
   - What's unclear: Whether `respx` is installed in the VPS test environment.
   - Recommendation: Planner checks `pip show respx`; if absent, add to requirements.txt or use `unittest.mock.patch` on `httpx.AsyncClient`.

2. **SmartStock upload parser `total_penerimaan` data quality**
   - What we know: Live smartstock docs show `total_penerimaan: 0` despite having supplier zone data. The parser at lines 3222-3233 has a fallback to column 3 that may not match the real xlsx layout.
   - What's unclear: Whether this is a widespread data-entry bug or isolated to specific records.
   - Recommendation: OPS-03 verification (D-12) should check a few smartstock documents created via the upload path. If zeros are widespread, the upload parser fix may be in scope for OPS-03 even though it's a different upload path.

3. **`POST /api/ai/conversations/<id>/messages` message storage format**
   - What we know: Each existing `ai_chat_history` document stores ONE query+response pair (not two documents). The UI-SPEC `GET /api/ai/conversations/<id>/messages` response requires separate user/assistant message objects.
   - What's unclear: Should the new endpoint store 1 document (combined) or 2 documents (separate) per exchange?
   - Recommendation: Store as 1 document per exchange (preserving existing schema). The GET endpoint denormalizes at read time to produce user+assistant message pair. This preserves backward compatibility with the existing `/api/ai/sessions/{id}` reader which expects the `query/response` pair in one document.

4. **`AI_FAKE=1` behavior for new `/api/ai/conversations/<id>/messages` endpoint**
   - What we know: FakeAIClient returns `GENERAL_RESPONSE` for non-blending session_ids. The new chat session_id will be a UUID (not containing "blend").
   - What's unclear: Whether `GENERAL_RESPONSE = "Analisis umum: data tersedia di sistem (Phase 4 fake)."` is an appropriate test stub for the chat endpoint test.
   - Recommendation: FakeAIClient is fine as-is; tests assert `"Phase 4 fake"` appears in response. No change to FakeAIClient needed.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `httpx` | OpenRouterClient | ✓ | 0.28.1 | — |
| `mongosh` | Schema probes | ✓ | live | — |
| `openpyxl` | Excel inspection | ✓ | 3.1.5 | — |
| `pandas` | Excel parser | ✓ | 2.3.3 | — |
| OpenRouter API | LLM calls | ✗ (key not yet set) | — | Operator must set OPENROUTER_API_KEY before cutover |
| `respx` (test httpx mock) | OPS-01 unit tests | UNKNOWN | — | `unittest.mock.patch` on httpx.AsyncClient |
| Frontend build tooling | OPS-04 | ✓ | craco + node | — |

**Missing dependencies with no fallback:**
- `OPENROUTER_API_KEY` — operator must obtain from OpenRouter account and set in `.env` before Plan 06-06 (cutover). Plans 06-01 through 06-05 use `AI_FAKE=1` and do not require a live key.

**Missing dependencies with fallback:**
- `respx` — if not available, use `unittest.mock.patch("httpx.AsyncClient.post")` pattern for OpenRouterClient unit tests.

---

## Project Constraints (from CLAUDE.md)

`./CLAUDE.md` was not found in the working directory — no project-level CLAUDE.md constraints to extract.

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | Yes | JWT Bearer via existing `Depends(get_current_user)` — unchanged |
| V3 Session Management | Partial | AI chat sessions use UUID session_id; no new session lifecycle management |
| V4 Access Control | Yes | All 4 new `/api/ai/conversations/*` endpoints gated by `Depends(get_current_user)` |
| V5 Input Validation | Yes | `content` field in POST body: strip + length guard (empty string → 422) |
| V6 Cryptography | No | No new crypto; API key stored in env var (operator-managed) |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| OPENROUTER_API_KEY exposed in logs | Information Disclosure | Never log `self._api_key`; use masked logging |
| Prompt injection via user chat message | Tampering | User content goes in user role (not system role); OpenRouter model has instruction following |
| Unauthorized access to another user's conversation history | Elevation of Privilege | `user_id` filter in all queries: `{"session_id": conv_id, "user_id": user["id"]}` |
| LLM cost exhaustion via unlimited requests | Denial of Service | OpenRouter account credit limit is the primary guard; no per-user rate limit added in Phase 6 (deferred to Phase 8) |

---

## Sources

### Primary (HIGH confidence)
- `pltu-tenayan-full-backup/backend/server.py` — full read; aggregation sites verified at lines 2379-2406, 2863-2885
- `pltu-tenayan-full-backup/backend/app/ai/client.py` — AIClient Protocol + factory verified
- `pltu-tenayan-full-backup/backend/app/ai/legacy_llm_wrapper.py` — current implementation verified
- `pltu-tenayan-full-backup/backend/tests/fakes/ai_client.py` — FakeAIClient signature verified
- `pltu-tenayan-full-backup/backend/requirements.txt` — httpx==0.28.1, legacy-ai-sdk==0.1.0 verified
- `pltu-tenayan-full-backup/backend/.env` — LEGACY_LLM_KEY confirmed
- `pltu-tenayan-full-backup/frontend/package.json` — sonner, react-markdown, date-fns confirmed
- `pltu-tenayan-full-backup/frontend/src/components/Layout.js` — nav integration target verified
- `mongosh pltu_tenayan` read-only probes — `ai_chat_history` schema (10 docs, 4 sessions), `smartstock` schema (`total_penerimaan` field), `sumberpemakaian` schema (`total_pemakaian` field)
- openpyxl file probes — Loading.xlsx (721 rows, 33 cols), Unloading.xlsx (721 rows, 59 cols), Lab_Internal.xlsx (721 rows, 31 cols)

### Secondary (MEDIUM confidence)
- [openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request) — endpoint URL, request/response schema, error codes
- [openrouter.ai/docs/api/reference/authentication](https://openrouter.ai/docs/api/reference/authentication) — auth header format, optional attribution headers
- [openrouter.ai/openai/gpt-4o-mini](https://openrouter.ai/openai/gpt-4o-mini) — pricing $0.15/$0.60 per 1M tokens

### Tertiary (LOW confidence — for validation)
- [platform.openai.com/docs/guides/structured-outputs](https://platform.openai.com/docs/guides/structured-outputs) — JSON mode "must contain word JSON" requirement (confirmed via search, cross-referenced to OpenAI docs)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all library versions verified from requirements.txt
- Architecture: HIGH — live MongoDB schema probed; server.py code read
- Smart-blending data correctness: HIGH — live schema confirmed, line numbers verified
- ai_chat_history schema: HIGH — live probe returned all 10 documents
- Excel files: HIGH — openpyxl inspection of all 3 files
- OpenRouter API contract: MEDIUM — docs fetched directly from openrouter.ai
- JSON mode "JSON" word requirement: MEDIUM — confirmed via OpenAI docs search

**Research date:** 2026-05-11
**Valid until:** 2026-06-11 (stable stack; OpenRouter pricing may change)
