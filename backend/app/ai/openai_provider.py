from __future__ import annotations

import asyncio
from typing import Optional

from app.ai.llm_provider import LLMError, LLMProvider


class OpenAIProvider(LLMProvider):
    """Minimal chat-completions client so providers are swappable. Not exercised by the test-suite."""
    name = "openai"

    def __init__(self, api_key: str, model: str, timeout: float = 30.0, retries: int = 2):
        if not api_key:
            raise LLMError("OPENAI_API_KEY is not configured")
        self._key, self._model, self._timeout, self._retries = api_key, model, timeout, retries

    async def generate(self, system, messages, max_tokens=700, temperature: Optional[float] = None) -> str:
        import httpx
        body = {"model": self._model, "max_completion_tokens": max_tokens,
                "messages": [{"role": "system", "content": system}, *messages]}
        if temperature is not None:
            body["temperature"] = temperature
        for attempt in range(self._retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as c:
                    r = await c.post("https://api.openai.com/v1/chat/completions", json=body,
                                     headers={"Authorization": f"Bearer {self._key}"})
                if r.status_code in (429,) or r.status_code >= 500:
                    raise httpx.HTTPError(f"status {r.status_code}")
                if r.status_code >= 400:
                    raise LLMError(f"openai request rejected ({r.status_code})")
                text = (r.json()["choices"][0]["message"]["content"] or "").strip()
                if not text:
                    raise LLMError("empty completion")
                return text
            except httpx.HTTPError:
                if attempt == self._retries:
                    raise LLMError("openai unavailable")
                await asyncio.sleep(0.8 * (2 ** attempt))
        raise LLMError("openai unavailable")
