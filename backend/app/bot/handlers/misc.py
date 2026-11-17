from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot import texts
from app.bot.handlers.common import converse
from app.bot.keyboards import inline as kb
from app.knowledge.topics import TOPICS
from app.services.conversation_service import reset_conversation
from app.services.user_service import delete_user_data

router = Router()
router.message.filter(F.chat.type == "private")
_TITLES = dict(TOPICS)


@router.message(Command("profile"))
async def cmd_profile(m: Message, sender, db_user, profile):
    if not profile.onboarding_complete and profile.experience is None:
        await sender.send(m.chat.id, texts.NO_PROFILE, user_id=db_user.id)
        return
    await sender.send(m.chat.id, texts.profile_text(profile), user_id=db_user.id)


@router.message(Command("learn"))
async def cmd_learn(m: Message, sender, db_user):
    await sender.send(m.chat.id, texts.LEARN_PROMPT, reply_markup=kb.topics_kb(), user_id=db_user.id)


@router.callback_query(F.data.startswith("learn:"))
async def cb_learn(cb: CallbackQuery, sender, manager, session, db_user, profile, bot):
    await cb.answer()
    title = _TITLES.get(cb.data.split(":", 1)[1])
    if not title:
        return
    await converse(chat_id=cb.message.chat.id, text=f"Please explain this topic at my level: {title}",
                   shown_text=f"Learn: {title}", update_id=None, bot=bot, sender=sender, manager=manager,
                   session=session, db_user=db_user, profile=profile)


@router.message(Command("reset"))
async def cmd_reset(m: Message, state: FSMContext, sender, memory, session, db_user):
    await state.clear()
    old_ids, _ = await reset_conversation(session, db_user.id)
    for cid in old_ids:
        await memory.clear(cid)
    await sender.send(m.chat.id, texts.RESET_DONE, user_id=db_user.id)


@router.message(Command("delete_my_data"))
async def cmd_delete(m: Message, sender, db_user):
    await sender.send(m.chat.id, texts.DELETE_CONFIRM, reply_markup=kb.confirm_kb("delete", "Yes, delete", "No, keep"),
                      user_id=db_user.id)


@router.callback_query(F.data == "delete:yes")
async def cb_delete_yes(cb: CallbackQuery, state: FSMContext, sender, memory, session, db_user):
    await cb.answer()
    chat_id = cb.message.chat.id
    conv_ids = await delete_user_data(session, db_user)
    await session.commit()
    for cid in conv_ids:
        await memory.clear(cid)
    await state.clear()
    await sender.send(chat_id, texts.DELETE_DONE)  # user row is gone: nothing more to link


@router.callback_query(F.data == "delete:no")
async def cb_delete_no(cb: CallbackQuery, sender, db_user):
    await cb.answer()
    await sender.send(cb.message.chat.id, texts.DELETE_CANCELLED, user_id=db_user.id)
