from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, require
from app.api.security import has_role
from app.database.models import AdminUser, AuditLog, SupportRequest, TicketStatus, User
from app.support.ticket_manager import TicketError

router = APIRouter(prefix="/api/support", tags=["support"])


def _t(t: SupportRequest) -> dict:
    return {"id": t.id, "ticket_code": t.ticket_code, "user_id": t.user_id, "status": t.status.value,
            "assigned_to": t.assigned_to, "created_at": t.created_at, "updated_at": t.updated_at}


async def _load(db, admin: AdminUser, ticket_id: int) -> SupportRequest:
    t = await db.get(SupportRequest, ticket_id)
    if not t:
        raise HTTPException(404, "not found")
    if not has_role(admin.role.value, "admin") and t.assigned_to not in (None, admin.id):
        raise HTTPException(403, "ticket belongs to another educator")
    return t


@router.get("")
async def list_tickets(request: Request, status: str | None = None, limit: int = Query(50, le=200), offset: int = 0,
                       db: AsyncSession = Depends(get_db), admin=Depends(require("educator"))):
    if status and status not in {s.value for s in TicketStatus}:
        raise HTTPException(422, "bad status")
    rows = await request.app.state.tickets.list(db, status=status, admin_id=admin.id,
                                                scoped=not has_role(admin.role.value, "admin"),
                                                limit=limit, offset=offset)
    return [_t(t) for t in rows]


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: int, db: AsyncSession = Depends(get_db), admin=Depends(require("educator"))):
    t = await _load(db, admin, ticket_id)
    u = await db.get(User, t.user_id)
    return {**_t(t), "username": u.username if u else None, "context": t.context_snapshot}


class AssignIn(BaseModel):
    admin_id: int | None = None


@router.post("/{ticket_id}/assign")
async def assign(ticket_id: int, body: AssignIn, request: Request, db: AsyncSession = Depends(get_db),
                 admin=Depends(require("educator"))):
    t = await _load(db, admin, ticket_id)
    target = body.admin_id or admin.id
    if target != admin.id and not has_role(admin.role.value, "admin"):
        raise HTTPException(403, "only admins can assign to others")
    if not await db.get(AdminUser, target):
        raise HTTPException(404, "admin not found")
    try:
        request.app.state.tickets.assign(t, target)
    except TicketError as e:
        raise HTTPException(409, str(e))
    db.add(AuditLog(admin_id=admin.id, action="ticket_assign", target=t.ticket_code, detail={"to": target}))
    await db.commit()
    return _t(t)


class ReplyIn(BaseModel):
    text: str = Field(min_length=1, max_length=3000)


@router.post("/{ticket_id}/reply")
async def reply(ticket_id: int, body: ReplyIn, request: Request, db: AsyncSession = Depends(get_db),
                admin=Depends(require("educator"))):
    t = await _load(db, admin, ticket_id)
    try:
        ok, out = await request.app.state.tickets.deliver_reply(db, request.app.state.sender, t, body.text, admin.id)
    except TicketError as e:
        raise HTTPException(409, str(e))
    await db.commit()
    if ok:
        return {"delivered": True, **_t(t)}
    if out.result is not None and out.result.blocked:
        raise HTTPException(422, {"error": "blocked by compliance gate", "rules": out.result.matched_rules})
    raise HTTPException(502, "message could not be delivered to the user")


class StatusIn(BaseModel):
    status: TicketStatus


@router.patch("/{ticket_id}/status")
async def set_status(ticket_id: int, body: StatusIn, request: Request, db: AsyncSession = Depends(get_db),
                     admin=Depends(require("educator"))):
    t = await _load(db, admin, ticket_id)
    try:
        request.app.state.tickets.set_status(t, body.status)
    except TicketError as e:
        raise HTTPException(409, str(e))
    db.add(AuditLog(admin_id=admin.id, action="ticket_status", target=t.ticket_code, detail={"to": body.status.value}))
    await db.commit()
    return _t(t)
