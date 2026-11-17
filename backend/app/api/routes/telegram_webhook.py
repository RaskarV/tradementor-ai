import hmac
import logging

from aiogram.types import Update
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from app.config import get_settings

router = APIRouter()
log = logging.getLogger(__name__)


@router.post("/webhook/telegram")
async def telegram_webhook(request: Request, background: BackgroundTasks):
    s = get_settings()
    token = request.headers.get("x-telegram-bot-api-secret-token", "")
    if not hmac.compare_digest(token.encode(), s.telegram_webhook_secret.encode()):
        raise HTTPException(403, "forbidden")
    body = await request.body()
    if len(body) > s.max_request_bytes:
        raise HTTPException(413, "payload too large")
    try:
        update = Update.model_validate_json(body)
    except Exception:
        raise HTTPException(400, "bad update")
    # Telegram retries until it gets a 2xx; the NX key makes a retried update a no-op.
    if not await request.app.state.redis.set(f"upd:{update.update_id}", "1", nx=True, ex=86400):
        return {"ok": True, "duplicate": True}
    background.add_task(_process, request.app, update)
    return {"ok": True}


async def _process(app, update: Update) -> None:
    try:
        await app.state.dp.feed_update(app.state.bot, update)
    except Exception:
        log.exception("update processing failed")  # never surfaced to the user
