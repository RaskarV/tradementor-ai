from aiogram.fsm.state import State, StatesGroup


class Onboarding(StatesGroup):
    traded = State()
    experience = State()
    capital = State()
    goals = State()
    language = State()


class RiskFlow(StatesGroup):
    capital = State()
    pct = State()
    entry = State()
    stop = State()
    target = State()
