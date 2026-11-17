from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Conversation, Message


async def get_active_conversation(session: AsyncSession, user_id: int) -> Conversation:
    conv = await session.scalar(select(Conversation).where(Conversation.user_id == user_id,
                                                           Conversation.is_active.is_(True))
                                .order_by(Conversation.id.desc()).limit(1))
    if conv is None:
        conv = Conversation(user_id=user_id)
        session.add(conv)
        await session.flush()
    return conv


async def reset_conversation(session: AsyncSession, user_id: int) -> tuple[list[int], Conversation]:
    old = list((await session.scalars(select(Conversation.id).where(
        Conversation.user_id == user_id, Conversation.is_active.is_(True)))).all())
    await session.execute(update(Conversation).where(Conversation.user_id == user_id).values(is_active=False))
    new = Conversation(user_id=user_id)
    session.add(new)
    await session.flush()
    return old, new


async def add_message(session: AsyncSession, conversation_id: int, role: str, content: str, *,
                      update_id: int | None = None, original_draft: str | None = None,
                      decision: str | None = None, rules: list | None = None) -> int | None:
    """Returns the new message id, or None when update_id was already processed (duplicate delivery)."""
    values = dict(conversation_id=conversation_id, role=role, content=content, original_draft=original_draft,
                  compliance_decision=decision, compliance_rules=rules, telegram_update_id=update_id)
    stmt = insert(Message).values(**values)
    if update_id is not None:
        stmt = stmt.on_conflict_do_nothing(index_elements=[Message.telegram_update_id])
    return (await session.execute(stmt.returning(Message.id))).scalar_one_or_none()


async def recent_messages(session: AsyncSession, conversation_id: int, limit: int = 12) -> list[dict]:
    rows = (await session.execute(select(Message.role, Message.content).where(
        Message.conversation_id == conversation_id, Message.role.in_(("user", "assistant")))
        .order_by(Message.id.desc()).limit(limit))).all()
    return [{"role": r, "content": c} for r, c in reversed(rows)]
