from decimal import Decimal

import pytest

from app.services.risk.collateral import (
    CollateralRequirement,
    calculate_collateral_summary,
)


pytestmark = [pytest.mark.unit]


def test_collateral_summary_distinguishes_reserved_and_free_cash() -> None:
    summary = calculate_collateral_summary(
        account_id="acct-demo",
        total_cash=Decimal("10000"),
        existing_reserved_cash=Decimal("500"),
        requirements=(
            CollateralRequirement(
                source_id="put-1",
                source_type="short_option",
                required_cash=Decimal("2500"),
                description="Synthetic short put reserve",
            ),
            CollateralRequirement(
                source_id="scenario-1",
                source_type="assignment_scenario",
                required_cash=Decimal("1000"),
            ),
        ),
    )

    assert summary.option_collateral_required == Decimal("3500")
    assert summary.total_reserved_cash == Decimal("4000")
    assert summary.free_cash == Decimal("6000")
    assert summary.collateral_utilization == Decimal("0.4")
    assert summary.account_id == "acct-demo"


def test_collateral_summary_allows_negative_free_cash_as_risk_signal() -> None:
    summary = calculate_collateral_summary(
        account_id="acct-demo",
        total_cash=Decimal("1000"),
        requirements=(
            CollateralRequirement(
                source_id="put-1",
                source_type="short_option",
                required_cash=Decimal("2500"),
            ),
        ),
    )

    assert summary.total_reserved_cash == Decimal("2500")
    assert summary.free_cash == Decimal("-1500")
    assert summary.collateral_utilization == Decimal("2.5")


def test_zero_cash_with_reserved_collateral_uses_free_cash_as_overcommitment_signal() -> None:
    summary = calculate_collateral_summary(
        account_id="acct-demo",
        total_cash=Decimal("0"),
        requirements=(
            CollateralRequirement(
                source_id="put-1",
                source_type="short_option",
                required_cash=Decimal("2500"),
            ),
        ),
    )

    assert summary.total_reserved_cash == Decimal("2500")
    assert summary.free_cash == Decimal("-2500")
    assert summary.collateral_utilization == Decimal("0")


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"account_id": "", "total_cash": Decimal("1")}, "account_id"),
        ({"account_id": "acct", "total_cash": Decimal("-1")}, "total_cash"),
        (
            {
                "account_id": "acct",
                "total_cash": Decimal("1"),
                "existing_reserved_cash": Decimal("-1"),
            },
            "existing_reserved_cash",
        ),
    ],
)
def test_collateral_summary_rejects_invalid_inputs(kwargs, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        calculate_collateral_summary(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"source_id": "", "source_type": "short_option", "required_cash": Decimal("1")}, "source_id"),
        ({"source_id": "id", "source_type": "", "required_cash": Decimal("1")}, "source_type"),
        ({"source_id": "id", "source_type": "short_option", "required_cash": Decimal("-1")}, "required_cash"),
    ],
)
def test_collateral_requirement_rejects_invalid_inputs(kwargs, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        CollateralRequirement(**kwargs)
