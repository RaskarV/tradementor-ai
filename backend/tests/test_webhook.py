"""Webhook security tests. Needs fastapi + aiogram installed (run with pytest in your environment)."""
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import telegram_webhook

SECRET = "test-webhook-secret-123456"


class FakeRedis:
    def __init__(self):
        self.keys = set()

    async def set(self, k, v, nx=False, ex=None):
        if nx and k in self.keys:
            return None
        self.keys.add(k)
        return True


class FakeDP:
    def __init__(self):
        self.updates = []

    async def feed_update(self, bot, update):
        self.updates.append(update.update_id)


def make():
    app = FastAPI()
    app.state.redis, app.state.dp, app.state.bot = FakeRedis(), FakeDP(), object()
    app.include_router(telegram_webhook.router)
    return app, TestClient(app)


def upd(i=1):
    return json.dumps({"update_id": i, "message": {"message_id": 1, "date": 1, "chat": {"id": 5, "type": "private"},
                                                   "from": {"id": 5, "is_bot": False, "first_name": "A"}, "text": "hi"}})


def test_rejects_missing_or_wrong_secret():
    _, c = make()
    assert c.post("/webhook/telegram", content=upd()).status_code == 403
    assert c.post("/webhook/telegram", content=upd(), headers={"X-Telegram-Bot-Api-Secret-Token": "x"}).status_code == 403


def test_accepts_valid_update_and_dedupes_retries():
    app, c = make()
    h = {"X-Telegram-Bot-Api-Secret-Token": SECRET}
    assert c.post("/webhook/telegram", content=upd(7), headers=h).json() == {"ok": True}
    assert c.post("/webhook/telegram", content=upd(7), headers=h).json().get("duplicate") is True
    assert app.state.dp.updates == [7]


def test_rejects_malformed_and_oversized_payloads():
    _, c = make()
    h = {"X-Telegram-Bot-Api-Secret-Token": SECRET}
    assert c.post("/webhook/telegram", content="not json", headers=h).status_code == 400
    assert c.post("/webhook/telegram", content="x" * 2_000_000, headers=h).status_code == 413
