from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, require
from app.database.models import (ComplianceLog, Conversation, Decision, Message, SupportRequest, TicketStatus,
                                 User)

router = APIRouter(prefix="/api", tags=["overview"], dependencies=[Depends(require("educator"))])


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    count = lambda q: db.scalar(q)  # noqa: E731
    since = now - timedelta(days=14)
    msg_rows = (await db.execute(select(func.date_trunc("day", Message.created_at), func.count())
                                 .where(Message.created_at >= since, Message.role.in_(("user", "assistant")))
                                 .group_by(1))).all()
    blk_rows = (await db.execute(select(func.date_trunc("day", ComplianceLog.created_at), func.count())
                                 .where(ComplianceLog.created_at >= since, ComplianceLog.decision == Decision.blocked)
                                 .group_by(1))).all()
    msgs, blks = {d.date(): n for d, n in msg_rows}, {d.date(): n for d, n in blk_rows}
    series = []
    for i in range(14, -1, -1):
        d = (now - timedelta(days=i)).date()
        series.append({"date": d.isoformat(), "messages": msgs.get(d, 0), "blocked": blks.get(d, 0)})
    return {
        "total_users": await count(select(func.count(User.id))),
        "active_users": await count(select(func.count(User.id)).where(User.last_active_at >= now - timedelta(days=7))),
        "total_conversations": await count(select(func.count(Conversation.id))),
        "messages_processed": await count(select(func.count(ComplianceLog.id))),
        "messages_blocked": await count(select(func.count(ComplianceLog.id)).where(ComplianceLog.decision == Decision.blocked)),
        "pending_support": await count(select(func.count(SupportRequest.id)).where(SupportRequest.status == TicketStatus.pending)),
        "series": series,
    }
