"""Audit logging for compliance decisions. Standard library only."""
from __future__ import annotations

import json
import logging
from typing import Awaitable, Callable, Optional

from app.compliance.compliance_models import ComplianceResult

log = logging.getLogger("compliance")
Sink = Callable[[ComplianceResult, Optional[int], Optional[int]], Awaitable[None]]


class ComplianceLogger:
    def __init__(self, sink: Optional[Sink] = None):
        self._sink = sink

    async def record(self, result: ComplianceResult, user_id=None, conversation_id=None) -> None:
        log.info(json.dumps({
            "decision": result.verdict.value, "rules": result.matched_rules,
            "severity": result.severity.name if result.severity else None,
            "type": result.message_type, "user_id": user_id,
            "safe_alternative": result.used_safe_alternative}))
        if self._sink:
            try:
                await self._sink(result, user_id, conversation_id)
            except Exception:  # audit write failure must not hide the (already made) decision
                log.exception("compliance audit sink failed")
