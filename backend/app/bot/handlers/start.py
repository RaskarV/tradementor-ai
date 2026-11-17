from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot import texts
from app.bot.keyboards import inline as kb
from app.bot.parsing import parse_capital, parse_experience, parse_language, parse_traded
from app.bot.states import Onboarding

router = Router()
router.message.filter(F.chat.type == "private")


async def begin_onboarding(chat_id, state: FSMContext, sender, db_user):
    await state.clear()
    await sender.send(chat_id, texts.INTRO, user_id=db_user.id)
    await state.set_state(Onboarding.traded)
    await sender.send(chat_id, texts.Q_TRADED, reply_markup=kb.traded_kb(), user_id=db_user.id)


@router.message(CommandStart())
async def cmd_start(m: Message, state: FSMContext, sender, db_user, profile):
    if profile.onboarding_complete:
        await state.clear()
        await sender.send(m.chat.id, texts.WELCOME_BACK, user_id=db_user.id)
        return
    await begin_onboarding(m.chat.id, state, sender, db_user)


@router.message(Command("help"))
async def cmd_help(m: Message, sender, db_user):
    await sender.send(m.chat.id, texts.HELP, user_id=db_user.id)


# ---- step 1: traded before -------------------------------------------------------------------
async def _ask_experience(chat_id, state, sender, db_user):
    await state.set_state(Onboarding.experience)
    await sender.send(chat_id, texts.Q_EXPERIENCE, reply_markup=kb.experience_kb(), user_id=db_user.id)


@router.callback_query(F.data.startswith("ob:traded:"))
async def cb_traded(cb: CallbackQuery, state: FSMContext, sender, db_user, profile):
    await cb.answer()
    profile.has_traded = cb.data.endswith("yes")
    await _ask_experience(cb.message.chat.id, state, sender, db_user)


@router.message(StateFilter(Onboarding.traded), F.text)
async def txt_traded(m: Message, state: FSMContext, sender, db_user, profile):
    val = parse_traded(m.text)
    if val is None:
        await sender.send(m.chat.id, texts.Q_TRADED_RETRY, reply_markup=kb.traded_kb(), user_id=db_user.id)
        return
    profile.has_traded = val
    await _ask_experience(m.chat.id, state, sender, db_user)


# ---- step 2: experience ----------------------------------------------------------------------
async def _ask_capital(chat_id, state, sender, db_user):
    await state.set_state(Onboarding.capital)
    await sender.send(chat_id, texts.Q_CAPITAL, reply_markup=kb.skip_kb("ob:capital:skip"), user_id=db_user.id)


@router.callback_query(F.data.startswith("ob:exp:"))
async def cb_exp(cb: CallbackQuery, state: FSMContext, sender, db_user, profile):
    await cb.answer()
    profile.experience = cb.data.split(":", 2)[2]
    await _ask_capital(cb.message.chat.id, state, sender, db_user)


@router.message(StateFilter(Onboarding.experience), F.text)
async def txt_exp(m: Message, state: FSMContext, sender, db_user, profile):
    val = parse_experience(m.text)
    if val is None:
        await sender.send(m.chat.id, texts.Q_EXPERIENCE_RETRY, reply_markup=kb.experience_kb(), user_id=db_user.id)
        return
    profile.experience = val
    await _ask_capital(m.chat.id, state, sender, db_user)


# ---- step 3: optional capital ----------------------------------------------------------------
async def _ask_goals(chat_id, state, sender, db_user):
    await state.set_state(Onboarding.goals)
    await sender.send(chat_id, texts.Q_GOALS, reply_markup=kb.goals_kb(), user_id=db_user.id)


@router.callback_query(F.data == "ob:capital:skip")
async def cb_capital_skip(cb: CallbackQuery, state: FSMContext, sender, db_user):
    await cb.answer()
    await _ask_goals(cb.message.chat.id, state, sender, db_user)


@router.message(StateFilter(Onboarding.capital), F.text)
async def txt_capital(m: Message, state: FSMContext, sender, db_user, profile):
    val = parse_capital(m.text)
    if val is not None:
        profile.learning_capital = Decimal(val)
    await _ask_goals(m.chat.id, state, sender, db_user)  # never force financial info


# ---- step 4: goals ---------------------------------------------------------------------------
async def _ask_language(chat_id, state, sender, db_user):
    await state.set_state(Onboarding.language)
    await sender.send(chat_id, texts.Q_LANGUAGE, reply_markup=kb.language_kb(), user_id=db_user.id)


@router.callback_query(F.data.startswith("ob:goal:"))
async def cb_goal(cb: CallbackQuery, state: FSMContext, sender, db_user, profile):
    await cb.answer()
    profile.objectives = cb.data.split(":", 2)[2][:300]
    await _ask_language(cb.message.chat.id, state, sender, db_user)


@router.message(StateFilter(Onboarding.goals), F.text)
async def txt_goal(m: Message, state: FSMContext, sender, db_user, profile):
    profile.objectives = m.text.strip()[:300]
    await _ask_language(m.chat.id, state, sender, db_user)


# ---- step 5: language, then save -------------------------------------------------------------
async def _finish(chat_id, state, sender, db_user, profile, language):
    profile.language = language
    profile.onboarding_complete = True
    await state.clear()
    await sender.send(chat_id, texts.ONBOARD_DONE, user_id=db_user.id)


@router.callback_query(F.data.startswith("ob:lang:"))
async def cb_lang(cb: CallbackQuery, state: FSMContext, sender, db_user, profile):
    await cb.answer()
    await _finish(cb.message.chat.id, state, sender, db_user, profile, cb.data.split(":", 2)[2])


@router.message(StateFilter(Onboarding.language), F.text)
async def txt_lang(m: Message, state: FSMContext, sender, db_user, profile):
    await _finish(m.chat.id, state, sender, db_user, profile, parse_language(m.text))
