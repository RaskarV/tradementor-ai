"""Input parsing and validation for the risk calculator. Standard library only."""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


class CalcValidationError(ValueError):
    """Message is safe to show to the user."""


@dataclass(frozen=True)
class CalcLimits:
    min_risk_pct: Decimal = Decimal("0.1")
    max_risk_pct: Decimal = Decimal("5")
    max_capital: Decimal = Decimal("1000000000")
    max_price: Decimal = Decimal("10000000")


_SUFFIX = {"k": Decimal(1_000), "l": Decimal(100_000), "lakh": Decimal(100_000),
           "lac": Decimal(100_000), "m": Decimal(1_000_000), "cr": Decimal(10_000_000),
           "crore": Decimal(10_000_000)}


def parse_number(raw, field: str = "value") -> Decimal:
    """Parse '50000', '₹50,000', 'Rs. 50k', '1.5 lakh'. Rejects NaN, inf, negatives and zero."""
    if isinstance(raw, Decimal):
        value = raw
    else:
        s = str(raw).strip().lower().replace(",", "").replace("₹", "").replace("%", "")
        s = re.sub(r"^(?:rs\.?|inr)\s*", "", s).strip()
        m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([a-z]*)", s)
        if not m:
            raise CalcValidationError(f"I couldn't read {field} as a number. Try something like 50000 or 50k.")
        num, suffix = m.groups()
        if suffix and suffix not in _SUFFIX:
            raise CalcValidationError(f"I couldn't read {field} as a number. Try something like 50000 or 50k.")
        try:
            value = Decimal(num) * _SUFFIX.get(suffix, Decimal(1))
        except InvalidOperation:
            raise CalcValidationError(f"I couldn't read {field} as a number.")
    if not value.is_finite():
        raise CalcValidationError(f"{field} must be a finite number.")
    if value <= 0:
        raise CalcValidationError(f"{field} must be greater than zero.")
    return value


def validate_inputs(capital, risk_pct, entry, stop, target, limits: CalcLimits) -> None:
    if capital > limits.max_capital:
        raise CalcValidationError("That capital amount is above the calculator's limit.")
    if not (limits.min_risk_pct <= risk_pct <= limits.max_risk_pct):
        raise CalcValidationError(
            f"Risk percentage must be between {limits.min_risk_pct}% and {limits.max_risk_pct}%.")
    for name, p in (("entry price", entry), ("stop-loss price", stop), ("target price", target)):
        if p is not None and p > limits.max_price:
            raise CalcValidationError(f"The {name} is above the calculator's limit.")
    if entry == stop:
        raise CalcValidationError("Entry and stop-loss can't be the same price: there would be no "
                                  "distance to measure risk against.")
    if target is not None:
        is_long = stop < entry
        if is_long and target <= entry:
            raise CalcValidationError("For a stop-loss below entry, the target must be above entry.")
        if not is_long and target >= entry:
            raise CalcValidationError("For a stop-loss above entry, the target must be below entry.")
