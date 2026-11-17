import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.ai.conversation_manager import ConversationManager
from app.ai.llm_provider import get_provider
from app.ai.memory import ShortTermMemory
from app.api.routes import (auth, compliance_routes, conversations, health, knowledge, overview, settings_routes,
                            support, telegram_webhook, users)
from app.bot.factory import build_bot, build_dispatcher
from app.bot.sender import SafeSender
from app.compliance.compliance_engine import ComplianceEngine
from app.compliance.compliance_logger import ComplianceLogger
from app.config import get_settings
from app.database.session import SessionLocal, engine as db_engine
from app.knowledge.embeddings import get_embedder
from app.knowledge.retriever import Retriever
from app.notifications.telegram_alerts import AdminAlerts
from app.services.compliance_service import load_policy, make_sink, sync_builtin_rules
from app.services.settings_service import SettingsService
from app.support.ticket_manager import TicketManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    redis = Redis.from_url(s.redis_url, decode_responses=True, protocol=2)
    bot = build_bot(s.telegram_bot_token)

    settings_service = SettingsService(SessionLocal)
    await settings_service.refresh()
    async with SessionLocal() as session:
        await sync_builtin_rules(session)
        await session.commit()
        policy = await load_policy(session)
    compliance = ComplianceEngine(policy, logger=ComplianceLogger(make_sink(SessionLocal)))

    alerts = AdminAlerts(bot, s.admin_telegram_ids, settings_service.alert_enabled)
    sender = SafeSender(bot, compliance,
                        on_block=lambda chat_id, result, mtype: alerts.blocked(chat_id, result, mtype),
                        on_gate_failure=lambda chat_id, exc: alerts.compliance_failure(type(exc).__name__, chat_id))

    providers: dict = {}

    def provider_getter():
        name, model = settings_service.llm_choice()
        key = (name or s.llm_provider, model)
        if key not in providers:
            providers[key] = get_provider(s, name, model)
        return providers[key]

    retriever = Retriever(lambda: get_embedder(s))
    memory = ShortTermMemory(redis)
    manager = ConversationManager(provider_getter, retriever, memory, redis,
                                  extra_prompt_getter=settings_service.extra_prompt,
                                  on_repeated_errors=alerts.ai_errors)
    tickets = TicketManager()
    dp = build_dispatcher(redis, SessionLocal, s.rate_limit_per_minute, dict(
        sender=sender, manager=manager, tickets=tickets, alerts=alerts, memory=memory,
        settings_service=settings_service, admin_ids=s.admin_telegram_ids))

    app.state.__dict__.update(bot=bot, dp=dp, redis=redis, session_factory=SessionLocal, engine=compliance,
                              sender=sender, tickets=tickets, retriever=retriever,
                              settings_service=settings_service)
    refresher = asyncio.create_task(settings_service.run_refresh_loop())

    if s.public_base_url:
        try:
            await bot.set_webhook(f"{s.public_base_url.rstrip('/')}/webhook/telegram",
                                  secret_token=s.telegram_webhook_secret,
                                  allowed_updates=["message", "callback_query"])
            log.info("webhook registered")
        except Exception:
            log.exception("could not register the Telegram webhook")
    yield
    refresher.cancel()
    await bot.session.close()
    await redis.aclose()
    await db_engine.dispose()


app = FastAPI(title="TradeMentor AI", version="1.0.0", lifespan=lifespan, docs_url=None, redoc_url=None,
              openapi_url=None)
app.add_middleware(CORSMiddleware, allow_origins=[get_settings().dashboard_origin], allow_credentials=False,
                   allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"], allow_headers=["Authorization", "Content-Type"])


@app.middleware("http")
async def limits_and_headers(request: Request, call_next):
    try:
        too_big = int(request.headers.get("content-length") or 0) > get_settings().max_request_bytes
    except ValueError:
        too_big = True
    if too_big:
        return JSONResponse({"detail": "payload too large"}, status_code=413)
    resp = await call_next(request)
    resp.headers.update({"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store",
                         "Referrer-Policy": "no-referrer"})
    return resp


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    log.exception("unhandled error on %s", request.url.path)
    return JSONResponse({"detail": "internal error"}, status_code=500)  # no traces to clients


for r in (health.router, telegram_webhook.router, auth.router, overview.router, users.router, conversations.router,
          compliance_routes.router, support.router, knowledge.router, settings_routes.router):
    app.include_router(r)
