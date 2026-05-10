"""Wraps emergentintegrations.LlmChat behind AIClient (D-04, ADR-005).

Stateless per-call: the wrapper constructs a fresh LlmChat in each
send_message call so session-scoped fixtures don't need to share a
connection across the suite. No rename, no behavior change vs the
inline pattern currently in server.py.
"""
from emergentintegrations.llm.chat import LlmChat, UserMessage


class EmergentLLMClientWrapper:
    def __init__(self, api_key: str, provider: str = "gemini", model: str = "gemini-2.5-flash"):
        self._api_key = api_key
        self._provider = provider
        self._model = model

    async def send_message(
        self, session_id: str, system_prompt: str, user_message: str
    ) -> str:
        chat = LlmChat(
            api_key=self._api_key,
            session_id=session_id,
            system_message=system_prompt,
        ).with_model(self._provider, self._model)
        return await chat.send_message(UserMessage(text=user_message))
