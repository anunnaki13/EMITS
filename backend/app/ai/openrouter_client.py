"""OpenRouter LLM client.

Implements the AIClient Protocol defined in app/ai/client.py.
Retry-with-backoff (3 attempts, 1s/2s/4s) for 5xx + 429.
After exhaustion raises LLMUnavailableError -> FastAPI maps to HTTP 503.

Security note (T-06-01-01): api_key is NEVER logged or included in
exception messages. All error strings are static Indonesian copy per D-09.
"""
import os
import asyncio
import httpx


class LLMUnavailableError(Exception):
    """Raised when OpenRouter is unavailable after retries or on fatal error.

    FastAPI exception_handler in server.py maps this to HTTP 503 with
    Indonesian detail body (D-09).
    """

    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)


class OpenRouterClient:
    """httpx-based OpenRouter client implementing the AIClient Protocol.

    OpenRouter API contract (RESEARCH §Focus 1):
      POST https://openrouter.ai/api/v1/chat/completions
      Authorization: Bearer <key>
      HTTP-Referer: http://103.150.197.225:3013
      X-Title: EMITS PLTU Tenayan
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    RETRYABLE_STATUSES = {429, 500, 502, 503}
    INDONESIAN_UNAVAILABLE = (
        "Layanan AI sementara tidak tersedia. Silakan coba lagi sebentar."
    )

    def __init__(self, api_key: str, model: str = "openai/gpt-4o-mini"):
        self._api_key = api_key
        self._model = model

    async def send_message(
        self, session_id: str, system_prompt: str, user_message: str
    ) -> str:
        """Send a message to OpenRouter and return the text response.

        Retries up to 3 times (backoff: 1s, 2s, 4s) on 429/5xx.
        Raises LLMUnavailableError after exhaustion or on fatal status.
        """
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": "http://103.150.197.225:3013",
            "X-Title": "EMITS PLTU Tenayan",
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
        # JSON mode only for smart-blending sessions (RESEARCH Pitfall 2)
        if "smart-blending" in (session_id or ""):
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
                    return resp.json()["choices"][0]["message"]["content"]

                if resp.status_code == 401:
                    raise LLMUnavailableError(
                        self.INDONESIAN_UNAVAILABLE, status_code=401
                    )

                if resp.status_code == 402:
                    # Credit exhausted — no retry
                    raise LLMUnavailableError(
                        self.INDONESIAN_UNAVAILABLE, status_code=402
                    )

                if resp.status_code in self.RETRYABLE_STATUSES:
                    last_exc = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                    if attempt < 2:
                        await asyncio.sleep(2**attempt)  # 1s -> 2s -> (exhausted)
                    continue

                # Unexpected non-retryable status
                raise LLMUnavailableError(
                    self.INDONESIAN_UNAVAILABLE,
                    status_code=resp.status_code,
                )

            except LLMUnavailableError:
                raise
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < 2:
                    await asyncio.sleep(2**attempt)
                # continue to next attempt

        raise LLMUnavailableError(self.INDONESIAN_UNAVAILABLE) from last_exc
