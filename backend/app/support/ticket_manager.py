import logging

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.bot import texts
from app.database.models import AuditLog, Message, SupportRequest, TicketStatus, User
from app.support.states import can_transition, new_ticket_code

log = logging.getLogger(__name__)
OPEN = (TicketStatus.pending, TicketStatus.assigned, TicketStatus.answered)


class TicketError(ValueError):
    pass


class TicketManager:
    async def create(self, session, user: User, conversation_id: int | None, context: list) -> tuple:
        existing = await session.scalar(select(SupportRequest).where(
            SupportRequest.user_id == user.id, SupportRequest.status.in_(OPEN)).limit(1))
        if existing:
            return existing, False
        snapshot = "\n".join(f"{'User' if m['role'] == 'user' else 'Bot'}: {m['content']}"
                             for m in context[-10:])[:6000]
        for _ in range(5):
            t = SupportRequest(ticket_code=new_ticket_code(), user_id=user.id, conversation_id=conversation_id,
                               context_snapshot=snapshot or None)
            try:
                async with session.begin_nested():
                    session.add(t)
                    await session.flush()
                return t, True
            except IntegrityError:
                continue
        raise TicketError("could not allocate a ticket code")

    async def get_by_code(self, session, code: str) -> SupportRequest | None:
        return await session.scalar(select(SupportRequest).where(SupportRequest.ticket_code == code.upper()))

    def assign(self, ticket: SupportRequest, admin_id: int) -> None:
        if ticket.status == TicketStatus.closed:
            raise TicketError("ticket is closed")
        if ticket.status != TicketStatus.assigned:
            self._move(ticket, TicketStatus.assigned)
        ticket.assigned_to = admin_id

    def _move(self, ticket: SupportRequest, new: TicketStatus) -> None:
        if not can_transition(ticket.status.value, new.value):
            raise TicketError(f"cannot move a {ticket.status.value} ticket to {new.value}")
        ticket.status = new

    def set_status(self, ticket: SupportRequest, new: TicketStatus) -> None:
        self._move(ticket, new)

    async def list(self, session, *, status=None, admin_id=None, scoped=False, limit=50, offset=0):
        q = select(SupportRequest).order_by(SupportRequest.id.desc()).limit(limit).offset(offset)
        if status:
            q = q.where(SupportRequest.status == TicketStatus(status))
        if scoped:  # educators: only their own tickets plus unassigned pending ones
            q = q.where(or_(SupportRequest.assigned_to == admin_id, SupportRequest.status == TicketStatus.pending))
        return (await session.scalars(q)).all()

    async def deliver_reply(self, session, sender, ticket: SupportRequest, text: str, admin_id: int | None) -> tuple:
        """Educator text goes through the same gate; if it is blocked it is withheld, never rewritten."""
        if ticket.status == TicketStatus.closed:
            raise TicketError("ticket is closed")
        user = await session.get(User, ticket.user_id)
        if user is None:
            raise TicketError("user no longer exists")
        body = texts.EDUCATOR_PREFIX.format(code=ticket.ticket_code) + text.strip()
        out = await sender.send(user.telegram_id, body, message_type="educator_reply", user_id=user.id,
                                conversation_id=ticket.conversation_id, withhold_on_block=True)
        if not out.delivered:
            return False, out
        if ticket.conversation_id:
            session.add(Message(conversation_id=ticket.conversation_id, role="admin", content=body,
                                compliance_decision="cleared"))
        if ticket.status in (TicketStatus.pending,):
            self._move(ticket, TicketStatus.assigned)
        if ticket.status == TicketStatus.assigned:
            self._move(ticket, TicketStatus.answered)
        session.add(AuditLog(admin_id=admin_id, action="ticket_reply", target=ticket.ticket_code))
        return True, out
