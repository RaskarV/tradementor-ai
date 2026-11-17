"""Persistence glue for the (database-free) compliance engine."""
from sqlalchemy import select

from app.compliance.compliance_models import CompliancePolicy, CustomRule, Severity
from app.compliance.compliance_rules import BUILTIN_RULES
from app.database.models import BotSetting, ComplianceLog, ComplianceRule, Decision


def make_sink(session_factory):
    async def sink(result, user_id, conversation_id):
        async with session_factory() as s:
            s.add(ComplianceLog(
                user_id=user_id, conversation_id=conversation_id, decision=Decision(result.verdict.value),
                matched_rules=result.matched_rules, severity=result.severity.name if result.severity else None,
                excerpt=(result.excerpt or None), message_type=result.message_type,
                used_safe_alternative=result.used_safe_alternative))
            await s.commit()
    return sink


async def sync_builtin_rules(session) -> None:
    existing = set((await session.scalars(select(ComplianceRule.code))).all())
    for r in BUILTIN_RULES:
        if r.rule_id not in existing:
            session.add(ComplianceRule(code=r.rule_id, category=r.category, severity=r.severity.name,
                                       is_builtin=True, enabled=True))
    await session.flush()


async def load_policy(session) -> CompliancePolicy:
    defaults = {r.rule_id: r.severity for r in BUILTIN_RULES}
    rows = (await session.scalars(select(ComplianceRule))).all()
    disabled, overrides, custom = set(), {}, []
    for r in rows:
        if not r.enabled:
            disabled.add(r.code)
        if r.is_builtin:
            if r.code in defaults and Severity.parse(r.severity) != defaults[r.code]:
                overrides[r.code] = Severity.parse(r.severity)
        elif r.pattern:
            custom.append(CustomRule(r.code, r.pattern, Severity.parse(r.severity), r.category or "custom"))
    cfg = await session.get(BotSetting, "compliance")
    value = cfg.value if cfg else {}
    return CompliancePolicy(
        block_threshold=Severity.parse(value.get("block_threshold", "MEDIUM")),
        disabled_rules=frozenset(disabled), severity_overrides=overrides, custom_rules=tuple(custom),
        regulatory_phrases=tuple(value.get("regulatory_phrases", [])))
