from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.ai.llm_provider import LLMError, LLMProvider

log = logging.getLogger(__name__)


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, api_key: str, model: str, timeout: float = 30.0, retries: int = 2):
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is not configured")
        import anthropic  # lazy: keeps the rest of the app importable without the SDK
        self._anthropic = anthropic
        self._client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout, max_retries=0)
        self._model, self._retries = model, retries

    async def generate(self, system, messages, max_tokens=700, temperature: Optional[float] = None) -> str:
        a = self._anthropic
        kwargs = dict(model=self._model, system=system, messages=messages, max_tokens=max_tokens)
        if temperature is not None:
            kwargs["temperature"] = temperature
        last: Optional[Exception] = None
        for attempt in range(self._retries + 1):
            try:
                resp = await self._client.messages.create(**kwargs)
                text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text").strip()
                if not text:
                    raise LLMError("empty completion")
                return text
            except (a.RateLimitError, a.APIConnectionError, a.APITimeoutError) as e:
                last = e
            except a.APIStatusError as e:
                if e.status_code < 500:
                    raise LLMError(f"claude request rejected ({e.status_code})") from e
                last = e
            if attempt < self._retries:
                await asyncio.sleep(0.8 * (2 ** attempt))
        log.warning("claude failed after retries: %s", type(last).__name__)
        raise LLMError("claude unavailable") from last
