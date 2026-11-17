"""Provider-neutral LLM interface. Standard library only; vendors are imported lazily."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class LLMError(Exception):
    """Any provider failure. Never shown to users."""


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(self, system: str, messages: list, max_tokens: int = 700,
                       temperature: Optional[float] = None) -> str:
        """messages: [{'role': 'user'|'assistant', 'content': str}], starting with 'user'."""


def get_provider(settings, name: Optional[str] = None, model: Optional[str] = None) -> LLMProvider:
    name = (name or settings.llm_provider).lower()
    if name == "claude":
        from app.ai.claude_provider import ClaudeProvider
        return ClaudeProvider(settings.anthropic_api_key, model or settings.claude_model)
    if name == "openai":
        from app.ai.openai_provider import OpenAIProvider
        return OpenAIProvider(settings.openai_api_key, model or settings.openai_model)
    raise LLMError(f"unknown LLM provider: {name}")
