"""AIClient Protocol + provider (Phase 4 D-04, D-06).

Production code branches on AI_FAKE env var. When AI_FAKE=1, returns
FakeAIClient (test stub, no LLM budget consumed). Otherwise returns the
EmergentLLMClientWrapper that adapts emergentintegrations.LlmChat to
this interface. IMPLICIT-005 / ADR-005 boundary respected — no provider
migration in Phase 4.
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
    from app.ai.emergent_wrapper import EmergentLLMClientWrapper
    return EmergentLLMClientWrapper(
        api_key=os.environ.get("EMERGENT_LLM_KEY", "")
    )
