from decimal import Decimal

import pytest

from app.services.options.formulas import (
    annualized_roi,
    bid_ask_spread_percentage,
    breakeven_after_credit,
    downside_buffer,
    premium_capture,
    premium_yield,
    upside_breakeven_after_credit,
)


pytestmark = [pytest.mark.unit]


def test_premium_yield_uses_capital_at_risk_denominator() -> None:
    assert premium_yield(Decimal("250"), Decimal("10000")) == Decimal("0.025")


def test_annualized_roi_uses_days_held() -> None:
    result = annualized_roi(
        return_amount=Decimal("250"),
        capital_at_risk=Decimal("10000"),
        days_held=Decimal("30"),
    )

    assert result == Decimal("0.3041666666666666666666666668")


def test_annualized_roi_handles_negative_returns_without_forecasting() -> None:
    result = annualized_roi(
        return_amount=Decimal("-250"),
        capital_at_risk=Decimal("10000"),
        days_held=Decimal("30"),
    )

    assert result == Decimal("-0.3041666666666666666666666668")


def test_breakeven_after_credit_is_reference_minus_credit() -> None:
    assert breakeven_after_credit(Decimal("85"), Decimal("2.50")) == Decimal("82.50")


def test_breakeven_after_credit_is_directional_not_a_short_call_upper_boundary() -> None:
    downside_breakeven = breakeven_after_credit(Decimal("100"), Decimal("2"))
    upside_breakeven = upside_breakeven_after_credit(Decimal("100"), Decimal("2"))

    assert downside_breakeven == Decimal("98")
    assert upside_breakeven == Decimal("102")
    assert downside_breakeven != upside_breakeven


def test_downside_buffer_compares_breakeven_to_reference_price() -> None:
    assert downside_buffer(Decimal("100"), Decimal("85")) == Decimal("0.15")
    assert downside_buffer(Decimal("100"), Decimal("105")) == Decimal("-0.05")


def test_bid_ask_spread_percentage_uses_midpoint_denominator() -> None:
    assert bid_ask_spread_percentage(Decimal("2.40"), Decimal("2.60")) == Decimal("0.08")


def test_premium_capture_allows_losses_without_clamping() -> None:
    assert premium_capture(Decimal("2.50"), Decimal("0.50")) == Decimal("0.8")
    assert premium_capture(Decimal("2.50"), Decimal("3.00")) == Decimal("-0.2")


@pytest.mark.parametrize(
    ("fn", "args", "message"),
    [
        (premium_yield, (Decimal("-1"), Decimal("100")), "premium"),
        (premium_yield, (Decimal("1"), Decimal("0")), "capital_at_risk"),
        (annualized_roi, (Decimal("1"), Decimal("0"), Decimal("30")), "capital_at_risk"),
        (annualized_roi, (Decimal("1"), Decimal("100"), Decimal("0")), "days_held"),
        (breakeven_after_credit, (Decimal("0"), Decimal("1")), "reference_price"),
        (breakeven_after_credit, (Decimal("100"), Decimal("-1")), "credit"),
        (upside_breakeven_after_credit, (Decimal("0"), Decimal("1")), "reference_price"),
        (upside_breakeven_after_credit, (Decimal("100"), Decimal("-1")), "credit"),
        (downside_buffer, (Decimal("0"), Decimal("90")), "reference_price"),
        (downside_buffer, (Decimal("100"), Decimal("-1")), "breakeven_price"),
        (bid_ask_spread_percentage, (Decimal("-1"), Decimal("1")), "bid"),
        (bid_ask_spread_percentage, (Decimal("2"), Decimal("1")), "ask"),
        (bid_ask_spread_percentage, (Decimal("0"), Decimal("0")), "midpoint"),
        (premium_capture, (Decimal("0"), Decimal("1")), "initial_credit"),
        (premium_capture, (Decimal("1"), Decimal("-1")), "current_debit_to_close"),
    ],
)
def test_formulas_reject_invalid_inputs(fn, args, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        fn(*args)
