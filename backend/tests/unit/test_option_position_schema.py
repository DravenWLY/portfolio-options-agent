from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.option_position import OptionPositionCreate


pytestmark = pytest.mark.unit


def _contract_payload() -> dict:
    return {
        "occ_symbol": "VOO260116P00400000",
        "underlying_symbol": "VOO",
        "expiration_date": date(2026, 1, 16),
        "strike": Decimal("400"),
        "option_type": "put",
    }


def test_option_position_create_accepts_synthetic_snaptrade_source() -> None:
    payload = OptionPositionCreate(
        contract=_contract_payload(),
        position_side="short",
        quantity=Decimal("1"),
        average_price=Decimal("2.50"),
        market_value=Decimal("250.00"),
        source="snaptrade",
        source_ref="provider_option_demo",
        data_freshness_status="cached",
        raw_provider_payload={"provider_position_id": "demo_option_position"},
    )

    assert payload.contract.occ_symbol == "VOO260116P00400000"
    assert payload.position_side == "short"
    assert payload.status == "open"
    assert payload.source == "snaptrade"


def test_option_position_create_rejects_negative_quantity() -> None:
    with pytest.raises(ValidationError):
        OptionPositionCreate(contract=_contract_payload(), position_side="long", quantity=Decimal("-1"))


def test_option_position_create_rejects_invalid_side() -> None:
    with pytest.raises(ValidationError):
        OptionPositionCreate(contract=_contract_payload(), position_side="flat", quantity=Decimal("1"))
