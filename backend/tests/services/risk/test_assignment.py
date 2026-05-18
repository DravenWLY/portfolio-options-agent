from decimal import Decimal

import pytest

from app.services.risk.assignment import (
    AssignmentScenario,
    PositionHolding,
    project_assignment_scenario,
)


pytestmark = [pytest.mark.unit]


def test_short_put_assignment_projects_cash_outflow_and_new_shares() -> None:
    projection = project_assignment_scenario(
        cash=Decimal("10000"),
        holdings=(
            PositionHolding("VOO", Decimal("10"), Decimal("5000")),
        ),
        scenario=AssignmentScenario(
            action="short_put_assignment",
            underlying_symbol="HOOD",
            contracts=Decimal("1"),
            strike=Decimal("80"),
            projected_underlying_price=Decimal("77"),
        ),
    )

    assert projection.share_delta == Decimal("100")
    assert projection.cash_delta == Decimal("-8000")
    assert projection.projected_cash == Decimal("2000")
    hood = next(item for item in projection.holdings if item.symbol == "HOOD")
    assert hood.quantity == Decimal("100")
    assert hood.market_value == Decimal("7700")
    assert projection.projected_total_value == Decimal("14700")
    assert projection.largest_position_symbol == "HOOD"


def test_short_call_assignment_projects_share_removal_and_cash_inflow() -> None:
    projection = project_assignment_scenario(
        cash=Decimal("500"),
        holdings=(PositionHolding("HOOD", Decimal("100"), Decimal("7700")),),
        scenario=AssignmentScenario(
            action="short_call_assignment",
            underlying_symbol="HOOD",
            contracts=Decimal("1"),
            strike=Decimal("85"),
            projected_underlying_price=Decimal("85"),
        ),
    )

    assert projection.share_delta == Decimal("-100")
    assert projection.cash_delta == Decimal("8500")
    assert projection.projected_cash == Decimal("9000")
    assert projection.holdings == ()
    assert projection.projected_total_value == Decimal("9000")


def test_long_call_and_long_put_exercise_actions_are_supported() -> None:
    long_call = AssignmentScenario(
        action="long_call_exercise",
        underlying_symbol="MSFT",
        contracts=Decimal("2"),
        strike=Decimal("400"),
    )
    long_put = AssignmentScenario(
        action="long_put_exercise",
        underlying_symbol="MSFT",
        contracts=Decimal("2"),
        strike=Decimal("400"),
    )

    assert long_call.share_delta == Decimal("200")
    assert long_call.cash_delta == Decimal("-80000")
    assert long_put.share_delta == Decimal("-200")
    assert long_put.cash_delta == Decimal("80000")


def test_naked_short_call_assignment_is_explicitly_out_of_scope() -> None:
    with pytest.raises(ValueError, match="negative projected holding"):
        project_assignment_scenario(
            cash=Decimal("1000"),
            holdings=(PositionHolding("HOOD", Decimal("50"), Decimal("4000")),),
            scenario=AssignmentScenario(
                action="short_call_assignment",
                underlying_symbol="HOOD",
                contracts=Decimal("1"),
                strike=Decimal("85"),
            ),
        )


def test_assignment_reprices_only_scenario_underlying_and_keeps_other_values() -> None:
    projection = project_assignment_scenario(
        cash=Decimal("10000"),
        holdings=(
            PositionHolding("VOO", Decimal("10"), Decimal("5000")),
            PositionHolding("QQQ", Decimal("2"), Decimal("800")),
        ),
        scenario=AssignmentScenario(
            action="short_put_assignment",
            underlying_symbol="VOO",
            contracts=Decimal("1"),
            strike=Decimal("400"),
            projected_underlying_price=Decimal("390"),
        ),
    )

    voo = next(item for item in projection.holdings if item.symbol == "VOO")
    qqq = next(item for item in projection.holdings if item.symbol == "QQQ")
    assert voo.quantity == Decimal("110")
    assert voo.market_value == Decimal("42900")
    assert qqq.market_value == Decimal("800")
    assert projection.projected_total_value == Decimal("13700")


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: PositionHolding("", Decimal("1"), Decimal("1")), "symbol"),
        (lambda: PositionHolding("HOOD", Decimal("-1"), Decimal("1")), "quantity"),
        (lambda: PositionHolding("HOOD", Decimal("1"), Decimal("-1")), "market_value"),
        (
            lambda: AssignmentScenario("unsupported", "HOOD", Decimal("1"), Decimal("1")),
            "action",
        ),
        (
            lambda: AssignmentScenario("short_put_assignment", "", Decimal("1"), Decimal("1")),
            "symbol",
        ),
        (
            lambda: AssignmentScenario("short_put_assignment", "HOOD", Decimal("0"), Decimal("1")),
            "contracts",
        ),
        (
            lambda: AssignmentScenario("short_put_assignment", "HOOD", Decimal("1"), Decimal("0")),
            "strike",
        ),
    ],
)
def test_assignment_inputs_are_validated(factory, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        factory()
