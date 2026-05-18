"""Deterministic option metric formulas.

All functions use ``Decimal`` inputs and return raw Decimal ratios or currency
levels. For example, ``Decimal("0.025")`` represents 2.5%; presentation layers
are responsible for rounding and percent formatting.
"""

from decimal import Decimal


TRADING_YEAR_DAYS = Decimal("365")


def _require_positive(value: Decimal, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_non_negative(value: Decimal, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def premium_yield(premium: Decimal, capital_at_risk: Decimal) -> Decimal:
    """Return premium received divided by capital at risk.

    Inputs:
    - ``premium``: total option premium or credit received, in account currency.
    - ``capital_at_risk``: collateral, notional, or basis used as denominator.
    """

    _require_non_negative(premium, "premium")
    _require_positive(capital_at_risk, "capital_at_risk")
    return premium / capital_at_risk


def annualized_roi(return_amount: Decimal, capital_at_risk: Decimal, days_held: Decimal) -> Decimal:
    """Return simple non-compounded annualized ROI.

    This is a linear extrapolation of a realized or projected return. It is not
    a forecast, probability model, or compounded return calculation.

    Inputs:
    - ``return_amount``: realized/projected profit or loss, in account currency.
    - ``capital_at_risk``: capital basis used as denominator.
    - ``days_held``: holding period or days to expiration.
    """

    _require_positive(capital_at_risk, "capital_at_risk")
    _require_positive(days_held, "days_held")
    return (return_amount / capital_at_risk) * (TRADING_YEAR_DAYS / days_held)


def breakeven_after_credit(reference_price: Decimal, credit: Decimal) -> Decimal:
    """Return downside breakeven after receiving a credit.

    Use this only when credit reduces a downside cost basis or downside
    breakeven, such as a short put strike or stock basis after call premium.
    It is intentionally not the upper breakeven for a short call or call credit
    spread; use ``upside_breakeven_after_credit`` for that direction.
    """

    _require_positive(reference_price, "reference_price")
    _require_non_negative(credit, "credit")
    return reference_price - credit


def upside_breakeven_after_credit(reference_price: Decimal, credit: Decimal) -> Decimal:
    """Return upside breakeven after receiving a credit.

    Use this when the risk boundary is above the reference price, such as an
    uncovered short call or a call credit spread. Strategy evaluators decide
    whether this metric is appropriate for their structure.
    """

    _require_positive(reference_price, "reference_price")
    _require_non_negative(credit, "credit")
    return reference_price + credit


def downside_buffer(reference_price: Decimal, breakeven_price: Decimal) -> Decimal:
    """Return downside buffer as a ratio of reference price.

    ``Decimal("0.10")`` means the breakeven is 10% below the reference price.
    Negative values mean breakeven is above the reference price.
    """

    _require_positive(reference_price, "reference_price")
    if breakeven_price < 0:
        raise ValueError("breakeven_price must be non-negative")
    return (reference_price - breakeven_price) / reference_price


def bid_ask_spread_percentage(bid: Decimal, ask: Decimal) -> Decimal:
    """Return bid/ask spread divided by midpoint.

    Inputs are quote prices in account currency. The returned ratio is useful
    for liquidity rules; e.g. ``Decimal("0.10")`` means the spread is 10% of
    the midpoint.
    """

    _require_non_negative(bid, "bid")
    _require_non_negative(ask, "ask")
    if ask < bid:
        raise ValueError("ask must be greater than or equal to bid")
    midpoint = (bid + ask) / Decimal("2")
    _require_positive(midpoint, "midpoint")
    return (ask - bid) / midpoint


def premium_capture(initial_credit: Decimal, current_debit_to_close: Decimal) -> Decimal:
    """Return short-premium capture as a ratio of initial credit.

    ``Decimal("1")`` means 100% of the initial credit has been captured.
    Values below zero mean the position costs more to close than the original
    credit. Values above one mean the close cost is negative or adjusted by a
    credit event; callers should decide whether to clamp for display.
    """

    _require_positive(initial_credit, "initial_credit")
    _require_non_negative(current_debit_to_close, "current_debit_to_close")
    return (initial_credit - current_debit_to_close) / initial_credit
