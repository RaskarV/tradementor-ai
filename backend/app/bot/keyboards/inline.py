from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.knowledge.topics import TOPICS


def _kb(rows):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=t, callback_data=d) for t, d in r]
                                                 for r in rows])


def traded_kb():
    return _kb([[("Yes, I have", "ob:traded:yes"), ("No, fresh start", "ob:traded:no")]])


def experience_kb():
    return _kb([[("Complete beginner", "ob:exp:complete_beginner")],
                [("Beginner with some knowledge", "ob:exp:beginner")],
                [("Intermediate trader", "ob:exp:intermediate")],
                [("Experienced trader", "ob:exp:experienced")]])


def skip_kb(data: str):
    return _kb([[("Skip", data)]])


def goals_kb():
    return _kb([[("Understand risk and position sizing", "ob:goal:Understand risk and position sizing")],
                [("Learn technical analysis", "ob:goal:Learn technical analysis")],
                [("Avoid scams and bad tips", "ob:goal:Avoid scams and bad tips")],
                [("Build a long-term plan", "ob:goal:Build a long-term plan")]])


def language_kb():
    return _kb([[("English", "ob:lang:English"), ("हिन्दी", "ob:lang:Hindi"), ("मराठी", "ob:lang:Marathi")]])


def confirm_kb(prefix: str, yes="Yes", no="No"):
    return _kb([[(yes, f"{prefix}:yes"), (no, f"{prefix}:no")]])


def topics_kb():
    rows, row = [], []
    for slug, title in TOPICS:
        row.append((title, f"learn:{slug}"))
        if len(row) == 1:
            rows.append(row); row = []
    return _kb(rows)
