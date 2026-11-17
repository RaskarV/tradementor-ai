"""Delete old conversation data per RETENTION_DAYS. Run daily (Railway/Render cron).
Removes messages, closed support tickets and compliance logs older than the window.
Usage: python -m scripts.purge_retention"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.config import get_settings
from app.database.models import ComplianceLog, Message, SupportRequest, TicketStatus
from app.database.session import SessionLocal


async def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=get_settings().retention_days)
    async with SessionLocal() as s:
        m = await s.execute(delete(Message).where(Message.created_at < cutoff))
        t = await s.execute(delete(SupportRequest).where(SupportRequest.status == TicketStatus.closed,
                                                         SupportRequest.updated_at < cutoff))
        c = await s.execute(delete(ComplianceLog).where(ComplianceLog.created_at < cutoff))
        await s.commit()
    print(f"purged messages={m.rowcount} tickets={t.rowcount} compliance_logs={c.rowcount}")


asyncio.run(main())
