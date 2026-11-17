import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent

from app.bot import texts
from app.bot.handlers import admin, chat, human, misc, risk, start
from app.bot.middlewares.core import DbSessionMiddleware, RateLimitMiddleware, UserContextMiddleware

log = logging.getLogger(__name__)


def build_bot(token: str) -> Bot:
    return Bot(token, default=DefaultBotProperties(parse_mode=None))  # plain text: no markup injection


def build_dispatcher(redis, session_factory, per_minute: int, deps: dict) -> Dispatcher:
    dp = Dispatcher(storage=RedisStorage(redis), **deps)
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(RateLimitMiddleware(redis, per_minute))
        observer.outer_middleware(DbSessionMiddleware(session_factory))
        observer.outer_middleware(UserContextMiddleware())
    # order matters: commands and FSM flows first, free-text catch-all last
    for r in (admin.router, start.router, risk.router, human.router, misc.router, chat.router):
        dp.include_router(r)

    @dp.errors()
    async def on_error(event: ErrorEvent, sender):
        log.error("handler error: %s", type(event.exception).__name__, exc_info=event.exception)
        u = event.update
        chat_id = (u.message.chat.id if u.message else u.callback_query.message.chat.id
                   if u.callback_query and u.callback_query.message else None)
        if chat_id:
            await sender.send(chat_id, texts.ERROR_GENERIC)  # never leak internals to users
        return True

    return dp
