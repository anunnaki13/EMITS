# AI Chat Conversations API Contract

**Version:** Phase 6 Plan 04
**Collection:** `ai_chat_history` (canonical, per ADR-012)
**Auth:** All endpoints require `Authorization: Bearer <JWT>` — `Depends(get_current_user)`

---

## Endpoints

### 1. GET /api/ai/conversations

List the current user's conversation sessions, newest first.

**Auth:** Required (JWT)
**Response:** `200 OK`

```json
[
  {
    "id": "tenayan-ai-<user_id>-<uuid4>",
    "title": "Berapa total stok batubara?",
    "last_message_at": "2026-05-10T11:00:00+00:00"
  }
]
```

**Notes:**
- `title` = first 50 chars of the first user message in that session; fallback `"Percakapan tanpa judul"` if no message yet.
- Returns at most 100 sessions.
- All sessions are filtered by `user_id` from the JWT — cross-user data not accessible.

**Error codes:**
- `401 Unauthorized` — missing or invalid JWT

---

### 2. POST /api/ai/conversations

Create a new empty conversation session.

**Auth:** Required (JWT)
**Request body:** (empty or `{}`)
**Response:** `201 Created`

```json
{
  "id": "tenayan-ai-<user_id>-<uuid4>",
  "title": "Percakapan tanpa judul",
  "last_message_at": "2026-05-10T12:00:00+00:00"
}
```

**Notes:**
- No document is inserted to `ai_chat_history` until the first message is sent.
- The returned `id` is the `session_id` to use in subsequent requests.

**Error codes:**
- `401 Unauthorized` — missing or invalid JWT

---

### 3. GET /api/ai/conversations/{id}/messages

Fetch paginated messages for a conversation, oldest first.

**Auth:** Required (JWT)
**Path param:** `id` — the `session_id` / conversation id
**Query params:**
- `before` (string, optional) — cursor for pagination; returns messages with `id < before`
- `limit` (int, optional, default=20, min=1, max=50)

**Response:** `200 OK`

```json
[
  {
    "id": "u-<doc_id>",
    "role": "user",
    "content": "Berapa total stok batubara?",
    "created_at": "2026-05-10T10:00:00+00:00"
  },
  {
    "id": "a-<doc_id>",
    "role": "assistant",
    "content": "Stok batubara saat ini adalah 50.000 ton.",
    "created_at": "2026-05-10T10:00:00+00:00"
  }
]
```

**Notes:**
- Each `ai_chat_history` document is denormalized into one `role=user` message and one `role=assistant` message (if `response` is non-null).
- User messages have `id` prefixed with `u-`; AI messages with `a-`.
- Filtered by `user_id` from JWT — cross-user sessions return 404.

**Error codes:**
- `401 Unauthorized` — missing or invalid JWT
- `404 Not Found` — session not found or belongs to a different user; body: `{"detail": "Percakapan tidak ditemukan"}`

---

### 4. POST /api/ai/conversations/{id}/messages

Send a user message. Backend calls LLM, persists the exchange, returns the AI response.

**Auth:** Required (JWT)
**Path param:** `id` — the `session_id` / conversation id
**Request body:**

```json
{ "content": "Berapa total stok batubara?" }
```

**Response:** `200 OK`

```json
{
  "id": "a-<doc_id>",
  "role": "assistant",
  "content": "Stok batubara saat ini adalah 50.000 ton.",
  "created_at": "2026-05-10T12:00:00+00:00"
}
```

**Notes:**
- `content` is stripped of whitespace; an empty or whitespace-only value returns `422`.
- The frontend is expected to show the user message optimistically; this endpoint returns only the AI response.
- LLM call uses `Depends(get_ai_client)` seam (OpenRouterClient in production; FakeAIClient under `AI_FAKE=1`).
- LLM unavailability raises `LLMUnavailableError` which the global handler maps to HTTP 503.
- One `ai_chat_history` document is inserted per exchange: `{id, user_id, session_id, module="general", query, response, parameters=null, created_at}`.

**Error codes:**
- `401 Unauthorized` — missing or invalid JWT
- `422 Unprocessable Entity` — `content` is empty or whitespace; body: `{"detail": "content is required"}`
- `503 Service Unavailable` — LLM unavailable after retries; body: `{"detail": "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar."}`

---

## Schema Migration Audit

**None required.** All 10 existing `ai_chat_history` records already have `session_id` present (verified via live read-only probe in RESEARCH §Focus 3). The `session_id` field is the natural conversation grouping key — no new fields added, no documents altered.

## Coexistence with /api/ai/sessions

The existing `/api/ai/sessions/*` endpoints remain unchanged (backward-compatible). Both endpoint groups read the same `ai_chat_history` collection filtered by `user_id`. The new `/api/ai/conversations/*` endpoints use the UI-SPEC response shape `{id, title, last_message_at}` while `/api/ai/sessions` uses the older paginated shape. See RESEARCH Pitfall 7.
