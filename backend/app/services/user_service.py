import hashlib
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AuditLog, Conversation, User, UserProfile


async def upsert_user(session: AsyncSession, telegram_id: int, username: str | None) -> User:
    now = datetime.now(timezone.utc)
    stmt = (insert(User).values(telegram_id=telegram_id, username=username, last_active_at=now)
            .on_conflict_do_update(index_elements=[User.telegram_id],
                                   set_={"username": username, "last_active_at": now})
            .returning(User.id))
    user_id = (await session.execute(stmt)).scalar_one()
    if not await session.scalar(select(UserProfile.id).where(UserProfile.user_id == user_id)):
        await session.execute(insert(UserProfile).values(user_id=user_id).on_conflict_do_nothing())
    await session.flush()
    session.expire_all()
    return (await session.execute(select(User).where(User.id == user_id))).unique().scalar_one()


def profile_dict(p: UserProfile) -> dict:
    return {"experience": getattr(p.experience, "value", p.experience), "has_traded": p.has_traded,
            "objectives": p.objectives, "language": p.language,
            "learning_capital": int(p.learning_capital) if p.learning_capital else None}


async def delete_user_data(session: AsyncSession, user: User) -> list[int]:
    """Hard-deletes the user and everything cascading from them. Returns conversation ids so the
    caller can purge Redis context. The audit entry stores only a salted-free hash, not the raw ID."""
    conv_ids = list((await session.scalars(select(Conversation.id).where(Conversation.user_id == user.id))).all())
    session.add(AuditLog(action="user_data_deleted",
                         target=hashlib.sha256(str(user.telegram_id).encode()).hexdigest()[:16]))
    await session.execute(delete(User).where(User.id == user.id))
    return conv_ids
