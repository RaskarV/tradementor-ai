"""Short-term conversation memory in Redis, with history normalisation for the LLM."""
from __future__ import annotations

import json
from typing import Any, Awaitable, Callable, Optional


def normalize_history(messages: list) -> list:
    """Merge consecutive same-role turns and make sure the list starts with a user turn."""
    out: list = []
    for m in messages:
        role = m.get("role")
        if role not in ("user", "assistant") or not m.get("content"):
            continue
        if out and out[-1]["role"] == role:
            out[-1] = {"role": role, "content": out[-1]["content"] + "\n" + m["content"]}
        else:
            out.append({"role": role, "content": m["content"]})
    while out and out[0]["role"] != "user":
        out.pop(0)
    return out


class ShortTermMemory:
    def __init__(self, redis: Any, max_messages: int = 12, ttl_seconds: int = 86400):
        self._r, self._max, self._ttl = redis, max_messages, ttl_seconds

    @staticmethod
    def key(conversation_id: int) -> str:
        return f"ctx:{conversation_id}"

    async def load(self, conversation_id: int,
                   loader: Optional[Callable[[], Awaitable[list]]] = None) -> list:
        raw = await self._r.lrange(self.key(conversation_id), 0, -1)
        if raw:
            return [json.loads(x) for x in raw]
        if loader is None:
            return []
        msgs = (await loader())[-self._max:]  # rebuild from the database after a Redis flush
        for m in msgs:
            await self._push(conversation_id, m)
        return msgs

    async def _push(self, conversation_id: int, msg: dict) -> None:
        k = self.key(conversation_id)
        await self._r.rpush(k, json.dumps(msg, ensure_ascii=False))
        await self._r.ltrim(k, -self._max, -1)
        await self._r.expire(k, self._ttl)

    async def append(self, conversation_id: int, role: str, content: str) -> None:
        await self._push(conversation_id, {"role": role, "content": content})

    async def clear(self, conversation_id: int) -> None:
        await self._r.delete(self.key(conversation_id))
