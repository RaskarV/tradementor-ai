"""Admin-only Telegram notifications.

This is the ONLY module besides bot/sender.py that may call send_message. It sends plain text
(no parse_mode) exclusively to configured administrator IDs, never to end users, so that
blocked-content excerpts can be reported without being filtered themselves."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Iterable

log = logging.getLogger(__name__)
_TYPE_LABELS = {"reply": "Reply", "follow_up": "Follow-up", "generated": "Generated Content",
                "educator_reply": "Educator Reply", "calculator": "Calculator", "system": "System"}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


class AdminAlerts:
    def __init__(self, bot: Any, admin_ids: Iterable[int], enabled: Callable[[str], bool] = lambda _k: True):
        self._bot, self._admins, self._enabled = bot, list(admin_ids), enabled

    async def _send_all(self, kind: str, text: str) -> int:
        if not self._enabled(kind):
            return 0
        delivered = 0
        for admin_id in self._admins:
            try:
                await self._bot.send_message(admin_id, text[:4000])
                delivered += 1
            except Exception as e:
                log.warning("admin alert to %s failed: %s", admin_id, type(e).__name__)
        return delivered

    async def blocked(self, user_telegram_id: int, result, message_type: str = "reply") -> int:
        text = ("BLOCKED OUTBOUND MESSAGE\n\n"
                f"User ID: {user_telegram_id}\n"
                f"Rule: {', '.join(result.matched_rules) or 'n/a'}\n"
                f"Matched Content: {(result.excerpt or '')[:300]}\n"
                f"Message Type: {_TYPE_LABELS.get(message_type, message_type)}\n"
                "Action: Blocked\n"
                f"Timestamp: {_now()}")
        return await self._send_all("blocked", text)

    async def human_request(self, ticket_code: str, user_telegram_id: int, username) -> int:
        who = f"@{username}" if username else f"ID {user_telegram_id}"
        return await self._send_all("human_request", (
            f"HUMAN SUPPORT REQUEST\n\nTicket: {ticket_code}\nUser: {who}\nStatus: Pending\n"
            f"Timestamp: {_now()}\n\nUse /assign {ticket_code} to take it, then /reply {ticket_code} <message>."))

    async def ai_errors(self, count: int) -> int:
        return await self._send_all("ai_errors", (
            f"AI SERVICE ERRORS\n\n{count} consecutive failures from the AI provider. "
            f"Users are receiving a temporary-unavailable message.\nTimestamp: {_now()}"))

    async def compliance_failure(self, error_name: str, user_telegram_id: int) -> int:
        return await self._send_all("compliance_failure", (
            f"COMPLIANCE VALIDATION FAILED\n\nUser ID: {user_telegram_id}\nError: {error_name}\n"
            f"Action: Message withheld; static error sent\nTimestamp: {_now()}"))

    async def escalation(self, ticket_code: str, note: str) -> int:
        return await self._send_all("escalation", (
            f"ESCALATED CONVERSATION\n\nTicket: {ticket_code}\nNote: {note[:500]}\nTimestamp: {_now()}"))

    async def direct(self, admin_chat_id: int, text: str) -> None:
        """Reply to an administrator who issued a command. Only called from admin-gated handlers."""
        try:
            await self._bot.send_message(admin_chat_id, text[:4000])
        except Exception as e:
            log.warning("admin reply failed: %s", type(e).__name__)
