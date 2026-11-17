"""SafeSender: the ONLY code path that delivers AI-generated text to a Telegram user.

Handlers receive a SafeSender, never a Bot. Everything goes through the ComplianceEngine first;
if the engine is unavailable the user gets a static error string and nothing unchecked is sent."""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

from app.compliance.compliance_models import ComplianceResult, ReviewContext

log = logging.getLogger(__name__)
STATIC_ERROR = "Something went wrong on our side. Please try again in a moment."
CHUNK = 4000

try:  # aiogram is a runtime dependency; tests may run without it
    from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
except Exception:  # pragma: no cover
    class TelegramForbiddenError(Exception): ...
    class TelegramRetryAfter(Exception):
        retry_after = 1


@dataclass
class SendOutcome:
    result: Optional[ComplianceResult]  # None when the gate was unavailable
    delivered: bool

    @property
    def text(self) -> str:
        return self.result.final_text if self.result else STATIC_ERROR


def split_text(text: str, limit: int = CHUNK) -> list:
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for para in text.split("\n"):
        while len(para) > limit:
            if cur:
                parts.append(cur); cur = ""
            parts.append(para[:limit]); para = para[limit:]
        if len(cur) + len(para) + 1 > limit:
            parts.append(cur); cur = para
        else:
            cur = f"{cur}\n{para}" if cur else para
    if cur:
        parts.append(cur)
    return parts


class SafeSender:
    def __init__(self, bot: Any, engine: Any,
                 on_block: Optional[Callable[[int, ComplianceResult, str], Awaitable[None]]] = None,
                 on_gate_failure: Optional[Callable[[int, Exception], Awaitable[None]]] = None):
        self._bot, self._engine = bot, engine
        self._on_block, self._on_gate_failure = on_block, on_gate_failure

    async def _deliver(self, chat_id: int, text: str, reply_markup=None) -> bool:
        parts = split_text(text)
        for i, part in enumerate(parts):
            markup = reply_markup if i == len(parts) - 1 else None
            for attempt in range(2):
                try:
                    await self._bot.send_message(chat_id, part, reply_markup=markup)
                    break
                except TelegramRetryAfter as e:
                    await asyncio.sleep(min(float(getattr(e, "retry_after", 1)), 10))
                except TelegramForbiddenError:
                    log.info("user %s blocked the bot", chat_id)
                    return False
                except Exception:
                    log.exception("telegram send failed")
                    return False
        return True

    async def send(self, chat_id: int, text: str, *, message_type: str = "reply", reply_markup=None,
                   user_id: Optional[int] = None, conversation_id: Optional[int] = None,
                   context: Optional[ReviewContext] = None, withhold_on_block: bool = False) -> SendOutcome:
        """withhold_on_block: for human-written text (educator replies) a block means 'do not deliver',
        not 'replace with a generic safe message'."""
        try:
            result = await self._engine.review(text, message_type=message_type, context=context,
                                               user_id=user_id, conversation_id=conversation_id)
        except Exception as exc:  # fail closed: never send unchecked text
            log.error("compliance gate unavailable: %s", type(exc).__name__)
            ok = await self._deliver(chat_id, STATIC_ERROR)
            if self._on_gate_failure:
                try:
                    await self._on_gate_failure(chat_id, exc)
                except Exception:
                    log.exception("gate-failure alert failed")
            return SendOutcome(None, ok)
        if result.blocked and self._on_block:
            try:
                await self._on_block(chat_id, result, message_type)
            except Exception:
                log.exception("block alert failed")
        if result.blocked and withhold_on_block:
            return SendOutcome(result, False)
        ok = await self._deliver(chat_id, result.final_text, reply_markup)
        return SendOutcome(result, ok)
