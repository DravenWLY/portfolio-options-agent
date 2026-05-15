from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.option_contract import OptionContractCreate


pytestmark = pytest.mark.unit


def test_option_contract_create_normalizes_symbols() -> None:
    payload = OptionContractCreate(
        occ_symbol=" voo260116p00400000 ",
        underlying_symbol=" voo ",
        expiration_date=date(2026, 1, 16),
        strike=Decimal("400"),
        option_type="put",
    )

    assert payload.occ_symbol == "VOO260116P00400000"
    assert payload.underlying_symbol == "VOO"
    assert payload.multiplier == Decimal("100")
    assert payload.style == "american"


def test_option_contract_create_rejects_invalid_option_type() -> None:
    with pytest.raises(ValidationError):
        OptionContractCreate(
            occ_symbol="VOO260116X00400000",
            underlying_symbol="VOO",
            expiration_date=date(2026, 1, 16),
            strike=Decimal("400"),
            option_type="unsupported",
        )


def test_option_contract_create_rejects_negative_strike() -> None:
    with pytest.raises(ValidationError):
        OptionContractCreate(
            occ_symbol="VOO260116P00400000",
            underlying_symbol="VOO",
            expiration_date=date(2026, 1, 16),
            strike=Decimal("-1"),
            option_type="put",
        )
