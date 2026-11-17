"""Runtime bot settings with a short in-process cache (refreshed by a background task)."""
import asyncio
import logging

from sqlalchemy import select

from app.database.models import BotSetting
from app.trading.validators import CalcLimits

log = logging.getLogger(__name__)
from decimal import Decimal

DEFAULTS = {
    "system_prompt_extra": "",
    "llm": {"provider": None, "model": None},
    "risk_limits": {"min_risk_pct": "0.1", "max_risk_pct": "5", "max_capital": "1000000000",
                    "max_price": "10000000"},
    "notifications": {"blocked": True, "human_request": True, "ai_errors": True,
                      "compliance_failure": True, "escalation": True},
    "compliance": {"block_threshold": "MEDIUM", "regulatory_phrases": []},
}


class SettingsService:
    def __init__(self, session_factory):
        self._sf = session_factory
        self._cache = {k: v for k, v in DEFAULTS.items()}

    async def refresh(self) -> None:
        try:
            async with self._sf() as s:
                rows = (await s.scalars(select(BotSetting))).all()
            merged = {k: v for k, v in DEFAULTS.items()}
            for r in rows:
                if r.key in DEFAULTS:
                    merged[r.key] = r.value
            self._cache = merged
        except Exception:
            log.exception("settings refresh failed; keeping previous values")

    async def run_refresh_loop(self, every: int = 30) -> None:
        while True:
            await asyncio.sleep(every)
            await self.refresh()

    def get(self, key):
        return self._cache.get(key, DEFAULTS.get(key))

    async def extra_prompt(self) -> str:
        return self.get("system_prompt_extra") or ""

    def llm_choice(self) -> tuple:
        v = self.get("llm") or {}
        return v.get("provider"), v.get("model")

    def alert_enabled(self, kind: str) -> bool:
        return bool((self.get("notifications") or {}).get(kind, True))

    def risk_limits(self) -> CalcLimits:
        v = {**DEFAULTS["risk_limits"], **(self.get("risk_limits") or {})}
        return CalcLimits(Decimal(str(v["min_risk_pct"])), Decimal(str(v["max_risk_pct"])),
                          Decimal(str(v["max_capital"])), Decimal(str(v["max_price"])))
