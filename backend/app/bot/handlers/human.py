from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot import texts
from app.bot.keyboards import inline as kb
from app.services.conversation_service import get_active_conversation, recent_messages

router = Router()
router.message.filter(F.chat.type == "private")


async def offer_human(chat_id, sender, db_user):
    await sender.send(chat_id, texts.HUMAN_OFFER, reply_markup=kb.confirm_kb("human", "Yes, submit request",
                                                                           "No thanks"), user_id=db_user.id)


@router.message(Command("human"))
async def cmd_human(m: Message, sender, db_user):
    await offer_human(m.chat.id, sender, db_user)


@router.callback_query(F.data == "human:yes")
async def cb_yes(cb: CallbackQuery, sender, tickets, alerts, session, db_user):
    await cb.answer()
    chat_id = cb.message.chat.id
    conv = await get_active_conversation(session, db_user.id)
    ctx = await recent_messages(session, conv.id, 10)
    ticket, created = await tickets.create(session, db_user, conv.id, ctx)
    await session.commit()  # make the ticket visible before admins are alerted
    if not created:
        await sender.send(chat_id, texts.HUMAN_EXISTS.format(code=ticket.ticket_code), user_id=db_user.id)
        return
    await alerts.human_request(ticket.ticket_code, cb.from_user.id, cb.from_user.username)
    await sender.send(chat_id, texts.HUMAN_CREATED.format(code=ticket.ticket_code), user_id=db_user.id)


@router.callback_query(F.data == "human:no")
async def cb_no(cb: CallbackQuery, sender, db_user):
    await cb.answer()
    await sender.send(cb.message.chat.id, texts.HUMAN_DECLINED, user_id=db_user.id)
