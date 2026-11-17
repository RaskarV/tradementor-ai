import logging
import time

from aiogram import BaseMiddleware

from app.bot import texts
from app.services.user_service import upsert_user

log = logging.getLogger(__name__)


def _chat_id(event):
    msg = getattr(event, "message", None) or event
    return getattr(getattr(msg, "chat", None), "id", None)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, redis, per_minute: int):
        self.redis, self.limit = redis, per_minute

    async def __call__(self, handler, event, data):
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)
        key = f"rl:{user.id}:{int(time.time() // 60)}"
        n = await self.redis.incr(key)
        if n == 1:
            await self.redis.expire(key, 90)
        if n > self.limit:
            if n == self.limit + 1 and _chat_id(event):
                await data["sender"].send(_chat_id(event), texts.RATE_LIMIT)
            return None
        return await handler(event, data)


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_factory):
        self.factory = session_factory

    async def __call__(self, handler, event, data):
        async with self.factory() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


class UserContextMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        tg = data.get("event_from_user")
        if tg is None or tg.is_bot:
            return await handler(event, data)
        user = await upsert_user(data["session"], tg.id, tg.username)
        data["db_user"], data["profile"] = user, user.profile
        return await handler(event, data)
