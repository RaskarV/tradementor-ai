from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, Update

from app.bot import texts
from app.bot.handlers.common import converse
from app.bot.handlers.human import offer_human
from app.bot.handlers.start import begin_onboarding
from app.bot.parsing import wants_human

router = Router()
router.message.filter(F.chat.type == "private")


@router.message(StateFilter(None), F.text, ~F.text.startswith("/"))
async def on_text(m: Message, state: FSMContext, event_update: Update, sender, manager, session, db_user, profile, bot):
    if not profile.onboarding_complete:
        await sender.send(m.chat.id, texts.ONBOARD_FIRST, user_id=db_user.id)
        await begin_onboarding(m.chat.id, state, sender, db_user)
        return
    if wants_human(m.text):
        await offer_human(m.chat.id, sender, db_user)
        return
    await converse(chat_id=m.chat.id, text=m.text, update_id=event_update.update_id, bot=bot, sender=sender,
                   manager=manager, session=session, db_user=db_user, profile=profile)


@router.message(StateFilter(None), ~F.text)
async def on_other(m: Message, sender, db_user):
    await sender.send(m.chat.id, "I can only read text messages for now. Please type your question.", user_id=db_user.id)
