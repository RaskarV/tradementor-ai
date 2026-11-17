"""Natural-language parsing for onboarding answers. Standard library only."""
from __future__ import annotations

import re
from typing import Optional

from app.trading.validators import CalcValidationError, parse_number

_NO = re.compile(r"\b(no|nope|never|not\s+yet|haven'?t|have\s+not|fresh|first\s+time|new\s+to)\b", re.I)
_YES = re.compile(r"\b(yes|yeah|yep|yup|i\s+have|i\s+do|traded|trading\s+for|some\s+trades|i\s+trade)\b", re.I)


def parse_traded(text: str) -> Optional[bool]:
    if _NO.search(text):
        return False
    if _YES.search(text):
        return True
    return None


def parse_experience(text: str) -> Optional[str]:
    t = text.lower()
    if re.search(r"complete|absolute|never|zero|fresh|no\s+experience|total", t):
        return "complete_beginner"
    if re.search(r"experienced|expert|advanced|professional|many\s+years|veteran", t):
        return "experienced"
    if re.search(r"intermediate|moderate|few\s+years|some\s+experience", t):
        return "intermediate"
    if re.search(r"beginner|some\s+knowledge|basic|learning|novice", t):
        return "beginner"
    return None


_LANGS = {"english": "English", "en": "English", "hindi": "Hindi", "हिन्दी": "Hindi", "हिंदी": "Hindi",
          "hi": "Hindi", "marathi": "Marathi", "मराठी": "Marathi", "mr": "Marathi", "hinglish": "Hinglish"}


def parse_language(text: str) -> str:
    t = text.strip().lower()
    if t in _LANGS:
        return _LANGS[t]
    for k, v in _LANGS.items():
        if len(k) > 3 and k in t:
            return v
    return re.sub(r"[^\w\s\u0900-\u097F-]", "", text).strip()[:30] or "English"


def parse_capital(text: str) -> Optional[str]:
    """Returns the amount as a plain decimal string, or None if the text isn't a usable number."""
    try:
        return str(parse_number(text, "capital"))
    except CalcValidationError:
        return None


_HUMAN = re.compile(r"(talk|speak|chat)\s+(to|with)\s+(a\s+|an\s+|some\s*(one|body)\s*|real\s+)?(human|person|"
                    r"educator|someone|somebody|team|mentor|teacher|agent)|\b(human|real\s+person|educator|"
                    r"mentor)\b.*\b(help|support|please|talk)\b|\bcontact\s+(support|team)\b", re.I)


def wants_human(text: str) -> bool:
    return bool(_HUMAN.search(text))
