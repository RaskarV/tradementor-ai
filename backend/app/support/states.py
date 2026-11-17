"""Support ticket state machine and codes. Standard library only."""
import secrets

ALLOWED = {
    "pending": {"assigned", "closed"},
    "assigned": {"answered", "closed", "pending"},
    "answered": {"assigned", "closed"},
    "closed": set(),
}
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def can_transition(current: str, new: str) -> bool:
    return new in ALLOWED.get(current, set())


def new_ticket_code() -> str:
    return "TM-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))
