from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, require
from app.api.routes.compliance_routes import reload_policy
from app.api.security import hash_password
from app.database.models import AdminRole, AdminUser, AuditLog, BotSetting
from app.services.settings_service import DEFAULTS

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/settings")
async def get_settings_(request: Request, _=Depends(require("admin"))):
    return {k: request.app.state.settings_service.get(k) for k in DEFAULTS}


class SettingIn(BaseModel):
    value: dict | str | list | bool | int | float | None


def _validate(key: str, v):
    if key == "system_prompt_extra" and not (isinstance(v, str) and len(v) <= 2000):
        raise HTTPException(422, "system_prompt_extra must be text up to 2000 characters")
    if key == "llm":
        if not isinstance(v, dict) or v.get("provider") not in (None, "claude", "openai"):
            raise HTTPException(422, "llm.provider must be claude or openai")
        v = {"provider": v.get("provider"), "model": (v.get("model") or None)}
    if key == "notifications":
        if not isinstance(v, dict) or not set(v) <= set(DEFAULTS["notifications"]):
            raise HTTPException(422, "unknown notification key")
        v = {k: bool(x) for k, x in v.items()}
    if key == "risk_limits":
        if not isinstance(v, dict) or not set(v) <= set(DEFAULTS["risk_limits"]):
            raise HTTPException(422, "unknown risk limit key")
        try:
            from decimal import Decimal
            [Decimal(str(x)) for x in v.values()]
        except Exception:
            raise HTTPException(422, "risk limits must be numbers")
    if key == "compliance":
        if not isinstance(v, dict) or v.get("block_threshold", "MEDIUM") not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            raise HTTPException(422, "block_threshold must be LOW, MEDIUM, HIGH or CRITICAL")
        phrases = v.get("regulatory_phrases", [])
        if not isinstance(phrases, list) or len(phrases) > 50 or any(not isinstance(p, str) or len(p) > 100 for p in phrases):
            raise HTTPException(422, "regulatory_phrases must be up to 50 short strings")
        v = {"block_threshold": v.get("block_threshold", "MEDIUM"), "regulatory_phrases": phrases}
    return v


@router.put("/settings/{key}")
async def put_setting(key: str, body: SettingIn, request: Request, db: AsyncSession = Depends(get_db),
                      admin=Depends(require("admin"))):
    if key not in DEFAULTS:
        raise HTTPException(404, "unknown setting")
    value = _validate(key, body.value)
    if key == "compliance" and value["block_threshold"] in ("HIGH", "CRITICAL") and admin.role.value != "owner":
        raise HTTPException(403, "only an owner can raise the block threshold above MEDIUM")
    row = await db.get(BotSetting, key)
    if row:
        row.value = value
    else:
        db.add(BotSetting(key=key, value=value))
    db.add(AuditLog(admin_id=admin.id, action="setting_update", target=key))
    await db.commit()
    await request.app.state.settings_service.refresh()
    if key == "compliance":
        try:
            await reload_policy(request)
        except ValueError as e:
            raise HTTPException(422, str(e))
    return {"ok": True}


class AdminIn(BaseModel):
    email: str = Field(max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=12, max_length=200)
    role: AdminRole = AdminRole.educator
    telegram_id: int | None = None


@router.get("/admins")
async def list_admins(db: AsyncSession = Depends(get_db), _=Depends(require("owner"))):
    return [{"id": a.id, "email": a.email, "role": a.role.value, "telegram_id": a.telegram_id, "is_active": a.is_active}
            for a in (await db.scalars(select(AdminUser).order_by(AdminUser.id))).all()]


@router.post("/admins", status_code=201)
async def create_admin(body: AdminIn, db: AsyncSession = Depends(get_db), admin=Depends(require("owner"))):
    if await db.scalar(select(AdminUser.id).where(AdminUser.email == body.email.lower())):
        raise HTTPException(409, "email already registered")
    a = AdminUser(email=body.email.lower(), password_hash=hash_password(body.password), role=body.role,
                  telegram_id=body.telegram_id)
    db.add(a)
    db.add(AuditLog(admin_id=admin.id, action="admin_create", target=body.email.lower()))
    await db.commit()
    return {"id": a.id}


class AdminPatch(BaseModel):
    role: AdminRole | None = None
    is_active: bool | None = None
    telegram_id: int | None = None


@router.patch("/admins/{admin_id}")
async def patch_admin(admin_id: int, body: AdminPatch, db: AsyncSession = Depends(get_db), me=Depends(require("owner"))):
    a = await db.get(AdminUser, admin_id)
    if not a:
        raise HTTPException(404, "not found")
    if a.id == me.id and (body.is_active is False or (body.role and body.role != AdminRole.owner)):
        raise HTTPException(409, "you cannot demote or deactivate yourself")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(a, k, v)
    db.add(AuditLog(admin_id=me.id, action="admin_update", target=a.email))
    await db.commit()
    return {"ok": True}
