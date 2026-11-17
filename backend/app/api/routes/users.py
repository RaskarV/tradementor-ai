from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import cast, func, or_, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, require
from app.api.security import has_role
from app.database.models import AdminUser, Conversation, Message, SupportRequest, User

router = APIRouter(prefix="/api/users", tags=["users"])


def _u(u: User) -> dict:
    p = u.profile
    return {"id": u.id, "telegram_id": u.telegram_id, "username": u.username,
            "experience": getattr(p.experience, "value", None) if p else None,
            "registered_at": u.created_at, "last_active_at": u.last_active_at}


@router.get("")
async def list_users(q: str | None = None, limit: int = Query(50, le=200), offset: int = 0,
                     db: AsyncSession = Depends(get_db), _=Depends(require("educator"))):
    stmt = select(User).order_by(User.id.desc()).limit(limit).offset(offset)
    if q:
        like = f"%{q[:64]}%"
        stmt = stmt.where(or_(User.username.ilike(like), cast(User.telegram_id, String).like(like)))
    total = await db.scalar(select(func.count(User.id)))
    return {"total": total, "items": [_u(u) for u in (await db.scalars(stmt)).unique().all()]}


async def can_read_history(db: AsyncSession, admin: AdminUser, user_id: int) -> bool:
    if has_role(admin.role.value, "admin"):
        return True
    return bool(await db.scalar(select(SupportRequest.id).where(
        SupportRequest.user_id == user_id, SupportRequest.assigned_to == admin.id).limit(1)))


@router.get("/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), admin=Depends(require("educator"))):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404, "not found")
    p = u.profile
    data = _u(u)
    data["profile"] = {"has_traded": p.has_traded, "objectives": p.objectives, "language": p.language,
                       "onboarding_complete": p.onboarding_complete}
    data["can_view_history"] = await can_read_history(db, admin, user_id)
    data["conversation_ids"] = list((await db.scalars(select(Conversation.id).where(
        Conversation.user_id == user_id).order_by(Conversation.id.desc()).limit(20))).all()) \
        if data["can_view_history"] else []
    return data
