from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import current_admin, get_db
from app.api.security import create_token, hash_password, verify_password
from app.config import get_settings
from app.database.models import AdminUser, AuditLog

router = APIRouter(prefix="/api/auth", tags=["auth"])
_DUMMY = hash_password("not-a-real-password")  # equalises timing for unknown emails


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=200)


@router.post("/login")
async def login(body: LoginIn, request: Request, db: AsyncSession = Depends(get_db)):
    redis = request.app.state.redis
    ip = request.client.host if request.client else "?"
    key = f"login:{ip}:{body.email.lower()}"
    attempts = await redis.incr(key)
    if attempts == 1:
        await redis.expire(key, 900)
    if attempts > 5:
        raise HTTPException(429, "too many attempts, try again later")
    admin = await db.scalar(select(AdminUser).where(AdminUser.email == body.email.lower()))
    ok = verify_password(body.password, admin.password_hash if admin else _DUMMY)
    if not (admin and ok and admin.is_active):
        db.add(AuditLog(action="login_failed", target=body.email.lower()[:128]))
        await db.commit()
        raise HTTPException(401, "invalid credentials")
    await redis.delete(key)
    db.add(AuditLog(admin_id=admin.id, action="login"))
    await db.commit()
    s = get_settings()
    return {"token": create_token(s.jwt_secret, admin.id, admin.role.value, s.jwt_ttl_minutes),
            "role": admin.role.value, "email": admin.email}


@router.get("/me")
async def me(admin: AdminUser = Depends(current_admin)):
    return {"id": admin.id, "email": admin.email, "role": admin.role.value}
