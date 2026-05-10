"""
Lifecycle and seam tests for Phase 4 infrastructure (Task 1 + Task 3).

Tests in this file verify:
  - server.py reads MONGO_TEST_DB_NAME at startup (Task 1)
  - get_ai_client() returns FakeAIClient when AI_FAKE=1 (Task 1)
  - FakeAIClient returns valid CONS-blending-ai-output JSON (Task 1)
  - FakeAIClient returns non-empty string for general queries (Task 1)
  - _backend_lifecycle spawned and backend responds on test port (Task 3)
  - MONGO_TEST_DB_NAME is exported for the session (Task 3)
"""
import importlib
import os
import pytest


def test_db_override_takes_effect(monkeypatch):
    """With MONGO_TEST_DB_NAME set, server.db.name uses the override."""
    monkeypatch.setenv("MONGO_TEST_DB_NAME", "pltu_tenayan_test_probe")
    monkeypatch.setenv("MONGO_URL", os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
    monkeypatch.setenv("DB_NAME", "pltu_tenayan")
    import server  # noqa: F401
    importlib.reload(server)
    assert server.db.name == "pltu_tenayan_test_probe"


def test_ai_fake_returns_fake_client(monkeypatch):
    """With AI_FAKE=1, get_ai_client() returns a FakeAIClient instance."""
    monkeypatch.setenv("AI_FAKE", "1")
    from app.ai.client import get_ai_client
    client = get_ai_client()
    assert type(client).__name__ == "FakeAIClient"
    monkeypatch.delenv("AI_FAKE", raising=False)


async def test_fake_blending_json_valid():
    """FakeAIClient returns valid CONS-blending-ai-output JSON for blending queries."""
    import json
    from tests.fakes.ai_client import FakeAIClient
    out = await FakeAIClient().send_message("blending-session", "smart blending system prompt", "any")
    parsed = json.loads(out)
    assert isinstance(parsed["recommendation"], list)
    assert isinstance(parsed["predicted_quality"], dict)
    assert isinstance(parsed["meets_target"], bool)
    assert isinstance(parsed["reasoning"], str)


async def test_fake_general_returns_string():
    """FakeAIClient returns a non-empty string for general (non-blending) queries."""
    from tests.fakes.ai_client import FakeAIClient
    out = await FakeAIClient().send_message("general-session", "general system prompt", "halo")
    assert isinstance(out, str) and len(out) > 0


def test_backend_lifecycle_spawns_and_responds(base_url):
    """The session-scoped fixture must have spawned a backend on the test port."""
    import requests
    r = requests.get(f"{base_url}/api/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"


def test_backend_has_test_db_env():
    """Sanity: the conftest exported MONGO_TEST_DB_NAME for the spawned subprocess."""
    assert os.environ.get("MONGO_TEST_DB_NAME", "").startswith("pltu_tenayan_test_")
