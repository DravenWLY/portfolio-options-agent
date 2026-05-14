from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.cash_balance import CashBalanceCreate


pytestmark = pytest.mark.unit


def test_cash_balance_create_accepts_synthetic_cash_categories() -> None:
    payload = CashBalanceCreate(
        total_cash=Decimal("10000.00"),
        reserved_collateral_cash=Decimal("2500.00"),
        free_cash=Decimal("6000.00"),
        premium_income_cash=Decimal("750.00"),
        dca_cash=Decimal("750.00"),
    )

    assert payload.total_cash == Decimal("10000.00")
    assert payload.reserved_collateral_cash == Decimal("2500.00")
    assert payload.as_of is not None


def test_cash_balance_create_rejects_negative_cash() -> None:
    with pytest.raises(ValidationError):
        CashBalanceCreate(total_cash=Decimal("-1.00"), free_cash=Decimal("0.00"))
