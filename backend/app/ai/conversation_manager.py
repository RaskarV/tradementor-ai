"""Builds a grounded draft reply. It does NOT send anything and does NOT do compliance:
every draft is untrusted and must go through SafeSender -> ComplianceEngine."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from app.ai.llm_provider import LLMProvider
from app.ai.memory import ShortTermMemory, normalize_history
from app.ai.prompt_templates import build_system_prompt, sanitize_user_text

log = logging.getLogger(__name__)
LLM_UNAVAILABLE_TEXT = ("I'm having trouble thinking this through right now. Please try again in a few "
                        "minutes, or use /risk for the position size calculator.")
ERROR_ALERT_THRESHOLD = 3


@dataclass
class Draft:
    text: str
    retrieved_text: str = ""
    sources: list = field(default_factory=list)
    llm_failed: bool = False


class ConversationManager:
    def __init__(self, provider_getter: Callable[[], LLMProvider], retriever: Any, memory: ShortTermMemory,
                 redis: Any, extra_prompt_getter: Optional[Callable[[], Awaitable[str]]] = None,
                 on_repeated_errors: Optional[Callable[[int], Awaitable[None]]] = None,
                 min_similarity: float = 0.35):
        self._provider_getter, self._retriever, self._memory, self._redis = provider_getter, retriever, memory, redis
        self._extra, self._on_errors, self._min_sim = extra_prompt_getter, on_repeated_errors, min_similarity

    async def generate_draft(self, *, conversation_id: int, user_text: str, profile: dict, session: Any = None,
                    history_loader=None) -> Draft:
        text = sanitize_user_text(user_text)
        history = await self._memory.load(conversation_id, history_loader)
        chunks = []
        try:
            chunks = [c for c in await self._retriever.search(session, text) if c.similarity >= self._min_sim]
        except Exception:
            log.exception("retrieval failed; continuing without reference material")
        extra = await self._extra() if self._extra else None
        system = build_system_prompt(profile, chunks, extra)
        messages = normalize_history(history + [{"role": "user", "content": text}])
        try:
            answer = await self._provider_getter().generate(system, messages)
        except Exception as e:
            log.warning("LLM failure: %s", type(e).__name__)
            n = await self._redis.incr("llm_errors")
            await self._redis.expire("llm_errors", 300)
            if n == ERROR_ALERT_THRESHOLD and self._on_errors:
                await self._on_errors(n)
            return Draft(LLM_UNAVAILABLE_TEXT, llm_failed=True)
        await self._redis.delete("llm_errors")
        sources = []
        for c in chunks:  # citations come from stored documents, never from model output
            label = f"{c.title} ({c.source_url})" if c.source_url else c.title
            if label not in sources:
                sources.append(label)
        if sources:
            answer += "\n\nSources: " + "; ".join(sources[:3])
        return Draft(answer, retrieved_text="\n".join(c.content for c in chunks), sources=sources[:3])

    async def remember(self, conversation_id: int, user_text: str, delivered_text: str) -> None:
        """Store what was actually delivered, so blocked drafts never re-enter the model context."""
        await self._memory.append(conversation_id, "user", sanitize_user_text(user_text))
        await self._memory.append(conversation_id, "assistant", delivered_text)
