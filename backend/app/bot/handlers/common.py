"""Shared conversation turn used by free text and /learn."""
import logging

from app.compliance.compliance_models import ReviewContext
from app.services.conversation_service import add_message, get_active_conversation, recent_messages
from app.services.user_service import profile_dict

log = logging.getLogger(__name__)


async def converse(*, chat_id: int, text: str, update_id: int | None, bot, sender, manager, session, db_user,
                   profile, shown_text: str | None = None) -> None:
    conv = await get_active_conversation(session, db_user.id)
    if await add_message(session, conv.id, "user", (shown_text or text)[:4000], update_id=update_id) is None:
        return  # duplicate delivery of the same Telegram update
    try:
        await bot.send_chat_action(chat_id, "typing")
    except Exception:
        pass
    draft = await manager.generate_draft(conversation_id=conv.id, user_text=text, profile=profile_dict(profile),
                                session=session, history_loader=lambda: recent_messages(session, conv.id, 12))
    out = await sender.send(chat_id, draft.text, user_id=db_user.id, conversation_id=conv.id,
                            context=ReviewContext(draft.retrieved_text))
    if out.result is None:
        await add_message(session, conv.id, "assistant", out.text, decision="error")
        return
    blocked = out.result.blocked
    await add_message(session, conv.id, "assistant", out.text, original_draft=draft.text if blocked else None,
                      decision="blocked" if blocked else "cleared", rules=out.result.matched_rules or None)
    if out.delivered:
        await manager.remember(conv.id, shown_text or text, out.text)
