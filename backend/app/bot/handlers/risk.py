from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot import texts
from app.bot.keyboards import inline as kb
from app.bot.states import RiskFlow
from app.trading.risk_calculator import calculate, explain
from app.trading.validators import CalcValidationError, parse_number

router = Router()
router.message.filter(F.chat.type == "private")


async def _run(chat_id, sender, db_user, limits, *args) -> bool:
    try:
        result = calculate(*args, limits=limits)
    except CalcValidationError as e:
        await sender.send(chat_id, f"{e}", message_type="calculator", user_id=db_user.id)
        return False
    await sender.send(chat_id, explain(result), message_type="calculator", user_id=db_user.id)
    return True


@router.message(Command("risk"))
async def cmd_risk(m: Message, command: CommandObject, state: FSMContext, sender, db_user, settings_service):
    await state.clear()
    if command.args:
        parts = command.args.replace(",", " ").split()
        if len(parts) in (4, 5):
            await _run(m.chat.id, sender, db_user, settings_service.risk_limits(), *parts)
        else:
            await sender.send(m.chat.id, texts.RISK_QUICK_HELP, user_id=db_user.id)
        return
    await sender.send(m.chat.id, texts.RISK_INTRO, user_id=db_user.id)
    await state.set_state(RiskFlow.capital)
    await sender.send(m.chat.id, texts.RISK_Q_CAPITAL, user_id=db_user.id)


@router.message(Command("cancel"))
async def cmd_cancel(m: Message, state: FSMContext, sender, db_user):
    if await state.get_state() is not None:
        await state.clear()
        await sender.send(m.chat.id, texts.RISK_CANCELLED, user_id=db_user.id)


async def _number(m, sender, db_user, label):
    try:
        return parse_number(m.text, label)
    except CalcValidationError as e:
        await sender.send(m.chat.id, f"{e}", message_type="calculator", user_id=db_user.id)
        return None


@router.message(StateFilter(RiskFlow.capital), F.text)
async def s_capital(m: Message, state: FSMContext, sender, db_user):
    v = await _number(m, sender, db_user, "capital")
    if v is None:
        return
    await state.update_data(capital=str(v))
    await state.set_state(RiskFlow.pct)
    await sender.send(m.chat.id, texts.RISK_Q_PCT, user_id=db_user.id)


@router.message(StateFilter(RiskFlow.pct), F.text)
async def s_pct(m: Message, state: FSMContext, sender, db_user, settings_service):
    v = await _number(m, sender, db_user, "risk percentage")
    if v is None:
        return
    lim = settings_service.risk_limits()
    if not (lim.min_risk_pct <= v <= lim.max_risk_pct):
        await sender.send(m.chat.id, f"Risk percentage must be between {lim.min_risk_pct}% and "
                                     f"{lim.max_risk_pct}%.", message_type="calculator", user_id=db_user.id)
        return
    await state.update_data(pct=str(v))
    await state.set_state(RiskFlow.entry)
    await sender.send(m.chat.id, texts.RISK_Q_ENTRY, user_id=db_user.id)


@router.message(StateFilter(RiskFlow.entry), F.text)
async def s_entry(m: Message, state: FSMContext, sender, db_user):
    v = await _number(m, sender, db_user, "entry price")
    if v is None:
        return
    await state.update_data(entry=str(v))
    await state.set_state(RiskFlow.stop)
    await sender.send(m.chat.id, texts.RISK_Q_STOP, user_id=db_user.id)


@router.message(StateFilter(RiskFlow.stop), F.text)
async def s_stop(m: Message, state: FSMContext, sender, db_user):
    v = await _number(m, sender, db_user, "stop-loss price")
    if v is None:
        return
    if v == Decimal((await state.get_data())["entry"]):
        await sender.send(m.chat.id, "Stop-loss can't equal the entry price. Please send a different stop-loss.",
                          message_type="calculator", user_id=db_user.id)
        return
    await state.update_data(stop=str(v))
    await state.set_state(RiskFlow.target)
    await sender.send(m.chat.id, texts.RISK_Q_TARGET, reply_markup=kb.skip_kb("risk:target:skip"), user_id=db_user.id)


async def _finish(chat_id, state, sender, db_user, settings_service, target):
    d = await state.get_data()
    ok = await _run(chat_id, sender, db_user, settings_service.risk_limits(), d["capital"], d["pct"], d["entry"],
                    d["stop"], target)
    if ok:
        await state.clear()
    return ok


@router.callback_query(F.data == "risk:target:skip")
async def cb_skip_target(cb: CallbackQuery, state: FSMContext, sender, db_user, settings_service):
    await cb.answer()
    await _finish(cb.message.chat.id, state, sender, db_user, settings_service, None)


@router.message(StateFilter(RiskFlow.target), F.text)
async def s_target(m: Message, state: FSMContext, sender, db_user, settings_service):
    v = await _number(m, sender, db_user, "target price")
    if v is not None:
        await _finish(m.chat.id, state, sender, db_user, settings_service, str(v))  # stays in state on error
