"""AIClient Protocol + provider factory (Phase 6, D-02 / D-04).

Production code branches on AI_FAKE env var. When AI_FAKE=1, returns
FakeAIClient (test stub, no LLM budget consumed). Otherwise returns
OpenRouterClient.

Phase 4 AI_FAKE=1 branch preserved VERBATIM (contract must not change).
"""
import os
from typing import Protocol, runtime_checkable


@runtime_checkable
class AIClient(Protocol):
    async def send_message(
        self, session_id: str, system_prompt: str, user_message: str
    ) -> str:
        """Send a message and return the LLM text response."""
        ...


def get_ai_client() -> AIClient:
    if os.environ.get("AI_FAKE") == "1":
        # Lazy import — never loaded in production.
        from tests.fakes.ai_client import FakeAIClient
        return FakeAIClient()
    from app.ai.openrouter_client import OpenRouterClient
    return OpenRouterClient(
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        model=os.environ.get("OPENROUTER_DEFAULT_MODEL", "openai/gpt-4o-mini"),
    )
