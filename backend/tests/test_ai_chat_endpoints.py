"""TEST-06-04: AI conversations endpoint coverage (D-18, OPS-04).

4 tests:
  1. test_list_conversations  — GET /api/ai/conversations
  2. test_get_messages        — GET /api/ai/conversations/{id}/messages
  3. test_create_conversation — POST /api/ai/conversations
  4. test_send_message        — POST /api/ai/conversations/{id}/messages

All run under AI_FAKE=1 (zero live LLM calls). Auth via admin JWT from conftest.

DEBT-03 regression: no ai_conversations collection references in server.py.
"""
import os
import uuid
import requests
import pymongo
import pytest


MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")


def _get_test_db():
    """Return the test database handle (per-session isolated DB from conftest)."""
    test_db_name = os.environ.get("MONGO_TEST_DB_NAME", "")
    assert test_db_name.startswith("pltu_tenayan_test_"), (
        f"Safety guard: MONGO_TEST_DB_NAME must be test DB, got {test_db_name!r}"
    )
    client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=3000)
    return client[test_db_name]


def _seed_chat_docs(user_id: str, session_a: str, session_b: str) -> None:
    """Seed deterministic ai_chat_history docs for the two sessions."""
    db = _get_test_db()
    # Remove any stale docs for these sessions
    db.ai_chat_history.delete_many({"session_id": {"$in": [session_a, session_b]}})
    now_base = "2026-05-10T10:00:00+00:00"
    now_later = "2026-05-10T11:00:00+00:00"
    docs = [
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_a,
            "module": "general",
            "query": "Berapa total stok batubara saat ini?",
            "response": "Stok batubara saat ini adalah 50.000 ton.",
            "parameters": None,
            "created_at": now_base,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_a,
            "module": "general",
            "query": "Bagaimana trennya?",
            "response": "Tren menurun selama 2 minggu terakhir.",
            "parameters": None,
            "created_at": now_later,
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_b,
            "module": "general",
            "query": "Apa rekomendasi blending terbaik?",
            "response": "Campurkan 60% LRC dan 40% HRC.",
            "parameters": None,
            "created_at": "2026-05-09T08:00:00+00:00",
        },
    ]
    db.ai_chat_history.insert_many(docs)


def _get_admin_user_id(base_url: str, admin_headers: dict) -> str:
    """Retrieve the admin user's id from /api/auth/me."""
    r = requests.get(f"{base_url}/api/auth/me", headers=admin_headers, timeout=10)
    assert r.status_code == 200, f"/api/auth/me failed: {r.status_code} {r.text[:200]}"
    return r.json()["id"]


def test_list_conversations(base_url, admin_headers):
    """GET /api/ai/conversations returns list of user's sessions newest-first."""
    user_id = _get_admin_user_id(base_url, admin_headers)
    session_a = f"tenayan-ai-{user_id}-{uuid.uuid4()}"
    session_b = f"tenayan-ai-{user_id}-{uuid.uuid4()}"
    _seed_chat_docs(user_id, session_a, session_b)

    r = requests.get(f"{base_url}/api/ai/conversations", headers=admin_headers, timeout=10)
    assert r.status_code == 200, f"GET /api/ai/conversations: {r.status_code} {r.text[:300]}"
    items = r.json()
    assert isinstance(items, list), f"Expected list, got {type(items)}"
    # Filter to only our seeded sessions (other sessions may exist from other tests)
    seeded_ids = {session_a, session_b}
    our_items = [i for i in items if i["id"] in seeded_ids]
    assert len(our_items) == 2, f"Expected 2 seeded sessions, found {len(our_items)} in {[i['id'] for i in items]}"
    for item in our_items:
        assert "id" in item, f"Missing 'id' key in {item}"
        assert "title" in item, f"Missing 'title' key in {item}"
        assert "last_message_at" in item, f"Missing 'last_message_at' key in {item}"

    # session_a was updated later (2026-05-10T11:00) vs session_b (2026-05-09T08:00)
    # So session_a should appear before session_b in newest-first order
    our_items_ordered = [i for i in items if i["id"] in seeded_ids]
    assert our_items_ordered[0]["id"] == session_a, (
        f"Expected session_a first (newest), got {our_items_ordered[0]['id']}"
    )
    # Title = first 50 chars of first query for session_a
    session_a_item = next(i for i in our_items if i["id"] == session_a)
    assert session_a_item["title"] == "Berapa total stok batubara saat ini?", (
        f"Unexpected title: {session_a_item['title']!r}"
    )


def test_get_messages(base_url, admin_headers):
    """GET /api/ai/conversations/{id}/messages returns chronological messages; cross-user 404."""
    user_id = _get_admin_user_id(base_url, admin_headers)
    session_a = f"tenayan-ai-{user_id}-{uuid.uuid4()}"
    session_b = f"tenayan-ai-{user_id}-{uuid.uuid4()}"
    _seed_chat_docs(user_id, session_a, session_b)

    r = requests.get(
        f"{base_url}/api/ai/conversations/{session_a}/messages?limit=20",
        headers=admin_headers,
        timeout=10,
    )
    assert r.status_code == 200, f"GET messages: {r.status_code} {r.text[:300]}"
    messages = r.json()
    assert isinstance(messages, list), f"Expected list, got {type(messages)}"
    # session_a has 2 docs each with user+assistant => up to 4 messages
    assert len(messages) >= 2, f"Expected >=2 messages, got {len(messages)}: {messages}"
    roles = {m["role"] for m in messages}
    assert roles <= {"user", "assistant"}, f"Unexpected roles: {roles}"
    for m in messages:
        assert "id" in m and "role" in m and "content" in m and "created_at" in m, (
            f"Message missing required keys: {m}"
        )
    # Chronological order: first message created_at <= last message created_at
    assert messages[0]["created_at"] <= messages[-1]["created_at"], (
        f"Messages not in chronological order: {messages[0]['created_at']} > {messages[-1]['created_at']}"
    )

    # Cross-user access: non-existent session (different user's session) should return 404
    alien_session = f"tenayan-ai-{uuid.uuid4()}-{uuid.uuid4()}"
    r2 = requests.get(
        f"{base_url}/api/ai/conversations/{alien_session}/messages",
        headers=admin_headers,
        timeout=10,
    )
    assert r2.status_code == 404, (
        f"Expected 404 for alien session, got {r2.status_code}: {r2.text[:200]}"
    )


def test_create_conversation(base_url, admin_headers):
    """POST /api/ai/conversations returns 201 with fresh session id and placeholder title."""
    r = requests.post(f"{base_url}/api/ai/conversations", headers=admin_headers, timeout=10)
    assert r.status_code == 201, f"POST /api/ai/conversations: {r.status_code} {r.text[:300]}"
    body = r.json()
    assert "id" in body, f"Missing 'id' in response: {body}"
    assert "title" in body, f"Missing 'title' in response: {body}"
    assert "last_message_at" in body, f"Missing 'last_message_at' in response: {body}"
    assert body["title"] == "Percakapan tanpa judul", (
        f"Expected placeholder title, got {body['title']!r}"
    )
    # Verify the returned id does NOT already exist in ai_chat_history (fresh session)
    new_id = body["id"]
    db = _get_test_db()
    existing = db.ai_chat_history.count_documents({"session_id": new_id})
    assert existing == 0, f"New session_id {new_id!r} already has {existing} docs in DB"


def test_send_message(base_url, admin_headers):
    """POST /api/ai/conversations/{id}/messages integrates FakeAIClient; persists to DB."""
    # Create a fresh conversation first
    r_create = requests.post(f"{base_url}/api/ai/conversations", headers=admin_headers, timeout=10)
    assert r_create.status_code == 201, f"Create conv failed: {r_create.status_code} {r_create.text}"
    conv_id = r_create.json()["id"]

    # Send a message
    payload = {"content": "Berapa total stok batubara?"}
    r = requests.post(
        f"{base_url}/api/ai/conversations/{conv_id}/messages",
        json=payload,
        headers=admin_headers,
        timeout=15,
    )
    assert r.status_code == 200, f"send_message: {r.status_code} {r.text[:300]}"
    body = r.json()
    assert body["role"] == "assistant", f"Expected role=assistant, got {body.get('role')!r}"
    assert body["content"], f"AI response content is empty"
    # FakeAIClient.GENERAL_RESPONSE = "Analisis umum: data tersedia di sistem (Phase 4 fake)."
    assert "Phase 4 fake" in body["content"], (
        f"Expected FakeAIClient marker in content, got: {body['content'][:200]}"
    )
    assert body["id"].startswith("a-"), f"Expected id to start with 'a-', got {body['id']!r}"

    # Verify exactly ONE doc persisted with session_id == conv_id
    db = _get_test_db()
    docs = list(db.ai_chat_history.find({"session_id": conv_id}))
    assert len(docs) == 1, f"Expected 1 doc in DB, found {len(docs)}"
    assert docs[0]["query"] == "Berapa total stok batubara?"
    assert docs[0]["response"] == body["content"]

    # Negative path: empty content -> 422
    r_empty = requests.post(
        f"{base_url}/api/ai/conversations/{conv_id}/messages",
        json={"content": ""},
        headers=admin_headers,
        timeout=10,
    )
    assert r_empty.status_code == 422, (
        f"Expected 422 for empty content, got {r_empty.status_code}: {r_empty.text[:200]}"
    )
