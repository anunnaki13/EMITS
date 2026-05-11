"""Unit tests for OpenRouterClient + factory (Phase 6, plan 06-01).

Uses unittest.mock.patch on httpx.AsyncClient (no respx dependency).
asyncio.sleep is patched to 0 to keep suite sub-second.

Maps to 06-VALIDATION.md rows 06-01-01 + 06-01-03.
"""
import os
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(status_code: int, json_body: dict = None):
    """Build a minimal httpx.Response mock."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or {}
    resp.request = MagicMock()
    return resp


SUCCESS_BODY = {
    "choices": [
        {"message": {"content": "Jawaban dari OpenRouter."}}
    ]
}


# ---------------------------------------------------------------------------
# Test 1: successful 200 response
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_message_success():
    from app.ai.openrouter_client import OpenRouterClient

    mock_resp = _mock_response(200, SUCCESS_BODY)

    with patch("httpx.AsyncClient") as MockClient:
        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_resp)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        client = OpenRouterClient(api_key="test-key", model="openai/gpt-4o-mini")
        result = await client.send_message(
            session_id="session-123",
            system_prompt="You are an analyst.",
            user_message="Summarise coal quality.",
        )

    assert result == "Jawaban dari OpenRouter."


# ---------------------------------------------------------------------------
# Test 2: retry exhaustion on persistent 503 -> LLMUnavailableError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retry_exhaustion():
    from app.ai.openrouter_client import OpenRouterClient, LLMUnavailableError

    mock_resp = _mock_response(503)

    with patch("httpx.AsyncClient") as MockClient, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_resp)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        client = OpenRouterClient(api_key="test-key")
        with pytest.raises(LLMUnavailableError) as exc_info:
            await client.send_message("s", "sys", "msg")

    assert "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar." in str(exc_info.value)
    # 3 attempts: sleep called after attempt 0 and attempt 1 (not after attempt 2)
    assert mock_sleep.call_count == 2


# ---------------------------------------------------------------------------
# Test 3: 402 raises immediately (no retry)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_402_immediate_unavailable():
    from app.ai.openrouter_client import OpenRouterClient, LLMUnavailableError

    mock_resp = _mock_response(402)

    with patch("httpx.AsyncClient") as MockClient, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_resp)
        MockClient.return_value.__aenter__ = AsyncMock(return_value=instance)
        MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

        client = OpenRouterClient(api_key="test-key")
        with pytest.raises(LLMUnavailableError) as exc_info:
            await client.send_message("s", "sys", "msg")

    assert exc_info.value.status_code == 402
    # No sleep — immediate failure
    mock_sleep.assert_not_called()
    # Only 1 HTTP call made
    instance.post.assert_called_once()


# ---------------------------------------------------------------------------
# Test 4: factory branches (AI_FAKE=1 -> FakeAIClient; else -> OpenRouterClient)
# ---------------------------------------------------------------------------

def test_factory_branches():
    """Verify get_ai_client() factory selects correct implementation."""
    from app.ai.client import get_ai_client
    from app.ai.openrouter_client import OpenRouterClient
    from tests.fakes.ai_client import FakeAIClient

    # AI_FAKE=1 branch
    with patch.dict(os.environ, {"AI_FAKE": "1"}):
        client = get_ai_client()
    assert isinstance(client, FakeAIClient), f"Expected FakeAIClient, got {type(client)}"

    # Production branch (OpenRouterClient)
    env_without_fake = {k: v for k, v in os.environ.items() if k != "AI_FAKE"}
    env_without_fake["OPENROUTER_API_KEY"] = "test-key"
    with patch.dict(os.environ, env_without_fake, clear=True):
        client = get_ai_client()
    assert isinstance(client, OpenRouterClient), f"Expected OpenRouterClient, got {type(client)}"
