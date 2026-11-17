"""Educational position-size calculator. Standard library only. Never executes trades."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Optional

from app.trading.validators import CalcLimits, parse_number, validate_inputs

DISCLAIMER = ("This is an educational calculation, not a recommendation to place a trade. A calculated "
              "quantity does not make a trade safe: brokerage, taxes, slippage and price gaps through "
              "your stop-loss can make the real loss larger than shown.")
_Q2 = Decimal("0.01")


def _m(x: Decimal) -> str:
    return f"₹{x.quantize(_Q2, ROUND_HALF_UP):,.2f}".replace(".00", "")


@dataclass(frozen=True)
class RiskResult:
    capital: Decimal
    risk_pct: Decimal
    entry: Decimal
    stop: Decimal
    target: Optional[Decimal]
    direction: str
    risk_amount: Decimal
    risk_per_unit: Decimal
    quantity: int
    position_value: Decimal
    max_theoretical_loss: Decimal
    stop_distance_pct: Decimal
    reward_per_unit: Optional[Decimal]
    reward_to_risk: Optional[Decimal]
    warnings: list = field(default_factory=list)


def calculate(capital, risk_pct, entry, stop, target=None, limits: Optional[CalcLimits] = None) -> RiskResult:
    limits = limits or CalcLimits()
    capital = parse_number(capital, "capital")
    risk_pct = parse_number(risk_pct, "risk percentage")
    entry = parse_number(entry, "entry price")
    stop = parse_number(stop, "stop-loss price")
    target = parse_number(target, "target price") if target not in (None, "") else None
    validate_inputs(capital, risk_pct, entry, stop, target, limits)

    risk_amount = capital * risk_pct / Decimal(100)
    risk_per_unit = abs(entry - stop)
    qty = int((risk_amount / risk_per_unit).to_integral_value(rounding=ROUND_DOWN))
    position_value = entry * qty
    max_loss = risk_per_unit * qty
    reward = abs(target - entry) if target is not None else None
    rr = (reward / risk_per_unit) if reward is not None else None
    stop_pct = risk_per_unit / entry * Decimal(100)

    warnings = []
    if qty < 1:
        warnings.append("Your risk budget is smaller than the risk on a single unit, so the quantity "
                        "rounds down to zero.")
    if position_value > capital:
        warnings.append("This position is larger than the capital you entered, which would need "
                        "borrowed money (leverage or margin) and adds risk.")
    if stop_pct < Decimal("0.1"):
        warnings.append("The stop-loss is very close to entry. Normal price movement and slippage "
                        "could trigger it.")
    return RiskResult(capital, risk_pct, entry, stop, target, "long" if stop < entry else "short",
                      risk_amount, risk_per_unit, qty, position_value, max_loss, stop_pct, reward, rr,
                      warnings)


def explain(r: RiskResult) -> str:
    lines = [
        "Position size (educational calculation)", "",
        f"Inputs: capital {_m(r.capital)}, risk {r.risk_pct.normalize():f}%, entry {_m(r.entry)}, "
        f"stop-loss {_m(r.stop)}" + (f", target {_m(r.target)}" if r.target is not None else ""),
        "",
        f"1) Risk amount = capital x risk% / 100 = {_m(r.capital)} x {r.risk_pct.normalize():f} / 100 "
        f"= {_m(r.risk_amount)}",
        f"2) Risk per unit = |entry - stop-loss| = |{_m(r.entry)} - {_m(r.stop)}| = {_m(r.risk_per_unit)}",
        f"3) Quantity = risk amount / risk per unit = {_m(r.risk_amount)} / {_m(r.risk_per_unit)} "
        f"= {r.quantity} units (rounded down)",
    ]
    if r.reward_per_unit is not None:
        lines += [
            f"4) Reward per unit = |target - entry| = {_m(r.reward_per_unit)}",
            f"5) Risk-to-reward = reward per unit / risk per unit = 1 : "
            f"{r.reward_to_risk.quantize(_Q2, ROUND_HALF_UP)}",
        ]
    lines += [
        "",
        f"Maximum theoretical loss before fees and slippage: {_m(r.max_theoretical_loss)}",
        f"Stop-loss distance: {_m(r.risk_per_unit)} ({r.stop_distance_pct.quantize(_Q2, ROUND_HALF_UP)}% "
        f"of entry)",
        f"Position quantity: {r.quantity} units, position value {_m(r.position_value)}",
    ]
    if r.warnings:
        lines += [""] + [f"Note: {w}" for w in r.warnings]
    lines += ["", DISCLAIMER]
    return "\n".join(lines)
