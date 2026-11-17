from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, require
from app.api.routes.users import can_read_history
from app.database.models import Conversation, Message, User

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(q: str | None = None, limit: int = Query(50, le=200), offset: int = 0,
                             db: AsyncSession = Depends(get_db), _=Depends(require("admin"))):
    stats = (select(Message.conversation_id.label("cid"), func.count().label("n"),
                    func.max(Message.created_at).label("last"),
                    func.count().filter(Message.compliance_decision == "blocked").label("blocked"))
             .group_by(Message.conversation_id))
    if q:
        stats = stats.where(Message.conversation_id.in_(
            select(Message.conversation_id).where(Message.content.ilike(f"%{q[:100]}%"))))
    s = stats.subquery()
    rows = (await db.execute(select(Conversation, User.username, User.telegram_id, s.c.n, s.c.last, s.c.blocked)
                             .join(s, s.c.cid == Conversation.id).join(User, User.id == Conversation.user_id)
                             .order_by(s.c.last.desc()).limit(limit).offset(offset))).all()
    return [{"id": c.id, "user_id": c.user_id, "username": un, "telegram_id": tg, "messages": n,
             "blocked": b, "last_message_at": last, "is_active": c.is_active} for c, un, tg, n, last, b in rows]


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: int, db: AsyncSession = Depends(get_db), admin=Depends(require("educator"))):
    conv = await db.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(404, "not found")
    if not await can_read_history(db, admin, conv.user_id):
        raise HTTPException(403, "no access to this user's history")
    msgs = (await db.scalars(select(Message).where(Message.conversation_id == conversation_id)
                             .order_by(Message.id))).all()
    return {"id": conv.id, "user_id": conv.user_id, "messages": [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at,
         "decision": m.compliance_decision, "rules": m.compliance_rules, "original_draft": m.original_draft}
        for m in msgs]}
