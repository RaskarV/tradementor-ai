from decimal import Decimal

import pytest

from app.compliance.compliance_engine import ComplianceEngine
from app.trading.risk_calculator import calculate, explain
from app.trading.validators import CalcLimits, CalcValidationError, parse_number


def test_spec_example():
    r = calculate(50000, 2, 500, 490)
    assert r.risk_amount == Decimal(1000) and r.risk_per_unit == Decimal(10)
    assert r.quantity == 100 and r.max_theoretical_loss == Decimal(1000)
    assert r.position_value == Decimal(50000) and r.warnings == []


def test_reward_to_risk_and_target():
    r = calculate(50000, 2, 500, 490, 530)
    assert r.reward_per_unit == Decimal(30) and r.reward_to_risk == Decimal(3)


def test_short_position_direction():
    r = calculate(100000, 1, 200, 205, 190)
    assert r.direction == "short" and r.quantity == 200 and r.reward_to_risk == Decimal(2)


def test_quantity_rounds_down_and_loss_never_exceeds_budget():
    r = calculate(50000, 2, 500, 493)
    assert r.quantity == 142 and r.max_theoretical_loss <= r.risk_amount


def test_zero_quantity_warns():
    r = calculate(1000, 1, 500, 100)
    assert r.quantity == 0 and any("zero" in w for w in r.warnings)


def test_position_larger_than_capital_warns():
    r = calculate(50000, 2, 500, 499)
    assert r.position_value > r.capital and any("borrowed" in w for w in r.warnings)


def _bad(*args):
    try:
        calculate(*args)
    except CalcValidationError:
        return True
    return False


def test_invalid_inputs_rejected():
    assert _bad(0, 2, 500, 490)
    assert _bad(-5, 2, 500, 490)
    assert _bad(50000, 0, 500, 490)
    assert _bad(50000, 50, 500, 490)          # above configured limit
    assert _bad(50000, 2, 500, 500)           # entry == stop
    assert _bad(50000, 2, 500, 490, 480)      # long target below entry
    assert _bad(50000, 2, 200, 205, 210)      # short target above entry
    assert _bad("abc", 2, 500, 490)
    assert _bad("nan", 2, 500, 490)
    assert _bad("inf", 2, 500, 490)
    assert _bad(50000, 2, 500, 490, "xyz")


def test_configurable_limits():
    assert _bad(50000, 3, 500, 490) is False
    try:
        calculate(50000, 3, 500, 490, limits=CalcLimits(max_risk_pct=Decimal(2)))
        raise AssertionError("should have been rejected")
    except CalcValidationError:
        pass


def test_parse_number_formats():
    assert parse_number("₹50,000") == 50000 and parse_number("50k") == 50000
    assert parse_number("1.5 lakh") == 150000 and parse_number("Rs. 2cr") == 20000000


def test_explanation_contains_required_parts():
    t = explain(calculate(50000, 2, 500, 490, 530))
    for s in ("Risk amount", "Risk per unit", "Quantity", "Maximum theoretical loss",
              "Stop-loss distance", "Risk-to-reward", "not a recommendation", "slippage"):
        assert s in t


async def test_calculator_output_passes_compliance():
    e = ComplianceEngine()
    for args in [(50000, 2, 500, 490), (50000, 2, 500, 490, 530), (1000, 1, 500, 100), (50000, 2, 500, 499)]:
        res = await e.review(explain(calculate(*args)), message_type="calculator")
        assert not res.blocked, res.matched_rules
