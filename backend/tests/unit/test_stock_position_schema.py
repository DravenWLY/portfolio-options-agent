from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.stock_position import StockPositionCreate


pytestmark = pytest.mark.unit


def test_stock_position_create_normalizes_symbol_and_defaults_source() -> None:
    payload = StockPositionCreate(symbol=" voo ", asset_type="etf", quantity=Decimal("12.5"))

    assert payload.symbol == "VOO"
    assert payload.asset_type == "etf"
    assert payload.quantity == Decimal("12.5")
    assert payload.source == "manual"
    assert payload.data_freshness_status == "unknown"


def test_stock_position_create_accepts_snaptrade_metadata() -> None:
    payload = StockPositionCreate(
        symbol="QQQ",
        asset_type="etf",
        quantity=Decimal("5"),
        market_price=Decimal("420.1234"),
        market_value=Decimal("2100.62"),
        source="snaptrade",
        source_ref="provider_position_demo",
        data_freshness_status="cached",
        raw_provider_payload={"provider_position_id": "demo_position"},
    )

    assert payload.source == "snaptrade"
    assert payload.source_ref == "provider_position_demo"
    assert payload.raw_provider_payload == {"provider_position_id": "demo_position"}


def test_stock_position_create_rejects_negative_quantity() -> None:
    with pytest.raises(ValidationError):
        StockPositionCreate(symbol="VOO", quantity=Decimal("-1"))


def test_stock_position_create_rejects_unsupported_source() -> None:
    with pytest.raises(ValidationError):
        StockPositionCreate(symbol="VOO", quantity=Decimal("1"), source="broker_secret")
