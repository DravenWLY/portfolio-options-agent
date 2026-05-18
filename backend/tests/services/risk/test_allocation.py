from decimal import Decimal

import pytest

from app.services.risk.allocation import (
    AllocationPosition,
    AllocationTarget,
    calculate_allocation_impact,
)


pytestmark = [pytest.mark.unit]


def test_allocation_impact_calculates_weights_and_target_drift() -> None:
    impact = calculate_allocation_impact(
        positions=(
            AllocationPosition("VOO", Decimal("6000")),
            AllocationPosition("QQQ", Decimal("3000")),
            AllocationPosition("CASH", Decimal("1000")),
        ),
        targets=(
            AllocationTarget("VOO", Decimal("0.50")),
            AllocationTarget("QQQ", Decimal("0.30")),
            AllocationTarget("CASH", Decimal("0.20")),
        ),
    )

    assert impact.total_value == Decimal("10000")
    assert impact.largest_position_symbol == "VOO"
    assert impact.largest_position_weight == Decimal("0.6")
    voo = next(item for item in impact.items if item.symbol == "VOO")
    cash = next(item for item in impact.items if item.symbol == "CASH")
    assert voo.actual_weight == Decimal("0.6")
    assert voo.drift == Decimal("0.10")
    assert cash.drift == Decimal("-0.10")
    assert cash.absolute_drift == Decimal("0.10")


def test_allocation_impact_allows_positions_without_targets() -> None:
    impact = calculate_allocation_impact(
        positions=(AllocationPosition("HOOD", Decimal("2500")),),
    )

    assert impact.items[0].target_weight is None
    assert impact.items[0].drift is None
    assert impact.largest_position_symbol == "HOOD"


def test_allocation_impact_emits_zero_position_items_for_missing_targets() -> None:
    impact = calculate_allocation_impact(
        positions=(AllocationPosition("VOO", Decimal("6000")),),
        targets=(
            AllocationTarget("VOO", Decimal("0.60")),
            AllocationTarget("QQQ", Decimal("0.40")),
        ),
    )

    qqq = next(item for item in impact.items if item.symbol == "QQQ")
    assert qqq.market_value == Decimal("0")
    assert qqq.actual_weight == Decimal("0")
    assert qqq.target_weight == Decimal("0.40")
    assert qqq.drift == Decimal("-0.40")
    assert qqq.absolute_drift == Decimal("0.40")


def test_allocation_impact_handles_empty_or_zero_value_portfolios() -> None:
    empty = calculate_allocation_impact(positions=())
    zero = calculate_allocation_impact(
        positions=(AllocationPosition("CASH", Decimal("0")),),
        targets=(AllocationTarget("CASH", Decimal("1")),),
    )

    assert empty.total_value == Decimal("0")
    assert empty.largest_position_symbol is None
    assert empty.items == ()
    assert zero.total_value == Decimal("0")
    assert zero.items[0].actual_weight == Decimal("0")
    assert zero.items[0].drift == Decimal("-1")


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: AllocationPosition("", Decimal("1")), "symbol"),
        (lambda: AllocationPosition("VOO", Decimal("-1")), "market_value"),
        (lambda: AllocationTarget("", Decimal("0.5")), "symbol"),
        (lambda: AllocationTarget("VOO", Decimal("-0.1")), "target_weight"),
        (lambda: AllocationTarget("VOO", Decimal("1.1")), "target_weight"),
    ],
)
def test_allocation_inputs_are_validated(factory, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        factory()
