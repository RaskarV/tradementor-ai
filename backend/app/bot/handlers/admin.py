"""Telegram-side admin commands. Replies to admins use alerts.direct (admin-only channel)."""
from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import select

from app.database.models import AdminUser, AuditLog, TicketStatus
from app.support.ticket_manager import TicketError

router = Router()


def is_admin(message: Message, admin_ids: list) -> bool:
    return message.chat.type == "private" and message.from_user is not None and message.from_user.id in admin_ids


router.message.filter(is_admin)


async def _admin_row(session, tg_id):
    return await session.scalar(select(AdminUser).where(AdminUser.telegram_id == tg_id, AdminUser.is_active.is_(True)))


@router.message(Command("tickets"))
async def cmd_tickets(m: Message, session, tickets, alerts):
    rows = await tickets.list(session, limit=15)
    lines = [f"{t.ticket_code}  {t.status.value}" for t in rows if t.status != TicketStatus.closed] or ["No open tickets."]
    await alerts.direct(m.chat.id, "Open support requests:\n" + "\n".join(lines))


@router.message(Command("assign"))
async def cmd_assign(m: Message, command: CommandObject, session, tickets, alerts):
    code = (command.args or "").split()[:1]
    admin = await _admin_row(session, m.from_user.id)
    if not code or admin is None:
        await alerts.direct(m.chat.id, "Usage: /assign TM-XXXXXX. Your Telegram ID must be linked to a dashboard "
                                       "admin account to assign tickets.")
        return
    t = await tickets.get_by_code(session, code[0])
    if t is None:
        await alerts.direct(m.chat.id, "Ticket not found.")
        return
    try:
        tickets.assign(t, admin.id)
    except TicketError as e:
        await alerts.direct(m.chat.id, str(e).capitalize() + ".")
        return
    session.add(AuditLog(admin_id=admin.id, action="ticket_assign", target=t.ticket_code))
    await alerts.direct(m.chat.id, f"{t.ticket_code} assigned to you. Reply with /reply {t.ticket_code} <message>.")


@router.message(Command("reply"))
async def cmd_reply(m: Message, command: CommandObject, session, tickets, alerts, sender):
    parts = (command.args or "").split(maxsplit=1)
    if len(parts) < 2:
        await alerts.direct(m.chat.id, "Usage: /reply TM-XXXXXX your message")
        return
    t = await tickets.get_by_code(session, parts[0])
    if t is None:
        await alerts.direct(m.chat.id, "Ticket not found.")
        return
    admin = await _admin_row(session, m.from_user.id)
    try:
        ok, out = await tickets.deliver_reply(session, sender, t, parts[1], admin.id if admin else None)
    except TicketError as e:
        await alerts.direct(m.chat.id, str(e).capitalize() + ".")
        return
    if ok:
        await alerts.direct(m.chat.id, f"Reply delivered to the user for {t.ticket_code}.")
    elif out.result is not None and out.result.blocked:
        await alerts.direct(m.chat.id, "NOT delivered: the compliance gate blocked your message ("
                            + ", ".join(out.result.matched_rules) + "). Please rephrase.")
    else:
        await alerts.direct(m.chat.id, "Could not deliver the message (the user may have blocked the bot).")


@router.message(Command("close"))
async def cmd_close(m: Message, command: CommandObject, session, tickets, alerts, sender):
    from app.bot import texts
    code = (command.args or "").split()[:1]
    t = await tickets.get_by_code(session, code[0]) if code else None
    if t is None:
        await alerts.direct(m.chat.id, "Usage: /close TM-XXXXXX")
        return
    try:
        tickets.set_status(t, TicketStatus.closed)
    except TicketError as e:
        await alerts.direct(m.chat.id, str(e).capitalize() + ".")
        return
    admin = await _admin_row(session, m.from_user.id)
    session.add(AuditLog(admin_id=admin.id if admin else None, action="ticket_close", target=t.ticket_code))
    from app.database.models import User
    u = await session.get(User, t.user_id)
    if u:
        await sender.send(u.telegram_id, texts.TICKET_CLOSED.format(code=t.ticket_code), user_id=u.id)
    await alerts.direct(m.chat.id, f"{t.ticket_code} closed.")
