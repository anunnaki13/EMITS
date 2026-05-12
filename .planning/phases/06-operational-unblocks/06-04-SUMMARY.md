---
phase: 06
plan: 04
subsystem: ai-chat-backend
tags: [ai-chat, conversations-api, ai_chat_history, ops-04]
dependency_graph:
  requires: [06-01]
  provides: [conversations-api-backend]
  affects: [server.py, test_ai_chat_endpoints.py, AI_CHAT_API.md]
tech_stack:
  added: []
  patterns: [cursor-pagination, flat-doc-denormalization, ai-client-protocol]
key_files:
  created:
    - pltu-tenayan-full-backup/backend/tests/test_ai_chat_endpoints.py
    - pltu-tenayan-full-backup/docs/audit/AI_CHAT_API.md
  modified:
    - pltu-tenayan-full-backup/backend/server.py
decisions:
  - "Single-doc-per-exchange pattern preserved; GET /messages denormalizes each doc into user+assistant messages at query time"
  - "send_conversation_message uses Request.json() (not Pydantic body model) to avoid FastAPI 422 shadowing the custom 422 for empty content"
  - "LLMUnavailableError bubbles to global exception handler from Plan 06-01 — no local try/except in send endpoint"
metrics:
  duration: "~15 min"
  completed_date: "2026-05-11"
  tasks: 2
  files_created: 2
  files_modified: 1
---

# Phase 6 Plan 04: AI Chat Conversations Backend Summary

One-liner: 4 `/api/ai/conversations/*` endpoints over `ai_chat_history` with JWT-scoped auth, cursor pagination, and FakeAIClient-tested send path.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 06-04-01 | 4 endpoints + AI_CHAT_API.md | bdda720 | server.py, docs/audit/AI_CHAT_API.md |
| 06-04-02 | 4 Wave-0 tests | bdda720 | tests/test_ai_chat_endpoints.py |

## Endpoint Signatures

```
GET  /api/ai/conversations               -> [{id, title, last_message_at}]  200
POST /api/ai/conversations               -> {id, title, last_message_at}    201
GET  /api/ai/conversations/{id}/messages -> [{id, role, content, created_at}] 200|404
POST /api/ai/conversations/{id}/messages -> {id, role, content, created_at} 200|422|503
```

## Schema Migration Audit

None required. All 10 existing `ai_chat_history` records have `session_id` (verified via live probe in RESEARCH §Focus 3). `session_id` is the natural grouping key — no schema change.

## Coexistence with /api/ai/sessions (RESEARCH Pitfall 7)

Both endpoint families read the same `ai_chat_history` collection filtered by `user_id`. `/api/ai/sessions` returns the older paginated shape; `/api/ai/conversations` returns the UI-SPEC `{id, title, last_message_at}` shape. No conflict.

## Test Results

```
tests/test_ai_chat_endpoints.py  4 passed
tests/test_ai_endpoints.py       9 passed
Total: 13 passed in 4.50s (AI_FAKE=1)
```

test_clean_checkout_gate pre-existing failure confirmed unchanged (4 files using pytest.skip() at module level with pytest >=9.x — documented in 06-01-SUMMARY.md, out of scope).

## Deviations from Plan

**[Rule 2 - Missing Input Handling] Used `Request.json()` instead of Pydantic body model**
- Found during: Task 06-04-01
- Issue: Defining a Pydantic model `class MessageBody(BaseModel): content: str` would make FastAPI return 422 for missing `content` key before the endpoint handler could return the custom 422 for empty string. Using `Request.json()` lets the handler validate and return the intended `{"detail": "content is required"}` for both missing and empty-string cases.
- Files modified: server.py (send_conversation_message)

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| threat_flag: elevation-of-privilege | server.py | Cross-user session access — mitigated: user_id filter on every query; cross-user returns 404 (T-06-04-01 mitigated, tested in test_get_messages negative path) |
| threat_flag: input-validation | server.py | Empty content body — mitigated: content.strip() empty -> 422 (T-06-04-03 mitigated, tested in test_send_message negative path) |

## Self-Check: PASSED

- [x] `pltu-tenayan-full-backup/backend/server.py` has 4 new endpoint decorators
- [x] `pltu-tenayan-full-backup/backend/tests/test_ai_chat_endpoints.py` exists (4 tests)
- [x] `pltu-tenayan-full-backup/docs/audit/AI_CHAT_API.md` exists
- [x] Inner repo commit exists: bdda720
- [x] `grep -c "ai_conversations" server.py` == 0 (DEBT-03 gate)
- [x] 13 tests pass under AI_FAKE=1
