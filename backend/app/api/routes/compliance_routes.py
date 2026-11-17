import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import Text, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, require
from app.compliance.compliance_rules import validate_pattern
from app.database.models import AuditLog, ComplianceLog, ComplianceRule, Decision
from app.services.compliance_service import load_policy

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/compliance", tags=["compliance"])


async def reload_policy(request: Request) -> None:
    async with request.app.state.session_factory() as s:
        policy = await load_policy(s)
    request.app.state.engine.update_policy(policy)  # raises ValueError on a bad pattern; old policy stays


@router.get("/logs")
async def logs(decision: str | None = None, rule: str | None = None, limit: int = Query(50, le=200), offset: int = 0,
               db: AsyncSession = Depends(get_db), _=Depends(require("admin"))):
    q = select(ComplianceLog).order_by(ComplianceLog.id.desc()).limit(limit).offset(offset)
    if decision in ("cleared", "blocked"):
        q = q.where(ComplianceLog.decision == Decision(decision))
    if rule:
        q = q.where(cast(ComplianceLog.matched_rules, Text).ilike(f"%{rule[:64]}%"))
    return [{"id": r.id, "user_id": r.user_id, "decision": r.decision.value, "rules": r.matched_rules,
             "severity": r.severity, "excerpt": r.excerpt, "message_type": r.message_type,
             "created_at": r.created_at} for r in (await db.scalars(q)).all()]


@router.get("/rules")
async def rules(db: AsyncSession = Depends(get_db), _=Depends(require("admin"))):
    return [{"code": r.code, "category": r.category, "severity": r.severity, "enabled": r.enabled,
             "is_builtin": r.is_builtin, "pattern": r.pattern}
            for r in (await db.scalars(select(ComplianceRule).order_by(ComplianceRule.id))).all()]


class RuleUpdate(BaseModel):
    enabled: bool | None = None
    severity: str | None = Field(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")


@router.put("/rules/{code}")
async def update_rule(code: str, body: RuleUpdate, request: Request, db: AsyncSession = Depends(get_db),
                      admin=Depends(require("admin"))):
    r = await db.scalar(select(ComplianceRule).where(ComplianceRule.code == code))
    if not r:
        raise HTTPException(404, "not found")
    weakening = (body.enabled is False) or (body.severity in ("LOW",) and r.is_builtin)
    if r.is_builtin and weakening and admin.role.value != "owner":
        raise HTTPException(403, "only an owner can disable or weaken a built-in rule")
    before = {"enabled": r.enabled, "severity": r.severity}
    if body.enabled is not None:
        r.enabled = body.enabled
    if body.severity:
        r.severity = body.severity
    db.add(AuditLog(admin_id=admin.id, action="compliance_rule_update", target=code,
                    detail={"before": before, "after": {"enabled": r.enabled, "severity": r.severity}}))
    await db.commit()
    try:
        await reload_policy(request)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"ok": True}


class CustomRuleIn(BaseModel):
    code: str = Field(pattern=r"^[A-Z][A-Z0-9_]{2,40}$")
    pattern: str = Field(max_length=300)
    severity: str = Field("HIGH", pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")


@router.post("/rules", status_code=201)
async def create_rule(body: CustomRuleIn, request: Request, db: AsyncSession = Depends(get_db),
                      admin=Depends(require("admin"))):
    try:
        validate_pattern(body.pattern)
    except ValueError as e:
        raise HTTPException(422, str(e))
    if await db.scalar(select(ComplianceRule.id).where(ComplianceRule.code == body.code)):
        raise HTTPException(409, "a rule with this code exists")
    db.add(ComplianceRule(code=body.code, category="custom", pattern=body.pattern, severity=body.severity))
    db.add(AuditLog(admin_id=admin.id, action="compliance_rule_create", target=body.code))
    await db.commit()
    await reload_policy(request)
    return {"ok": True}


@router.delete("/rules/{code}")
async def delete_rule(code: str, request: Request, db: AsyncSession = Depends(get_db), admin=Depends(require("admin"))):
    r = await db.scalar(select(ComplianceRule).where(ComplianceRule.code == code))
    if not r or r.is_builtin:
        raise HTTPException(404, "custom rule not found (built-in rules cannot be deleted)")
    await db.delete(r)
    db.add(AuditLog(admin_id=admin.id, action="compliance_rule_delete", target=code))
    await db.commit()
    await reload_policy(request)
    return {"ok": True}
