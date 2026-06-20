import pytest

from app.db.base import Base
from app.models.stock_position import StockPosition


pytestmark = pytest.mark.unit


def test_stock_position_model_is_registered_with_base_metadata() -> None:
    assert "stock_positions" in Base.metadata.tables


def test_stock_position_model_columns() -> None:
    columns = StockPosition.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "account_id",
        "sync_run_id",
        "symbol",
        "instrument_name",
        "asset_type",
        "quantity",
        "average_price",
        "cost_basis",
        "market_price",
        "market_value",
        "open_pnl",
        "currency",
        "source",
        "source_ref",
        "data_freshness_status",
        "raw_provider_payload",
        "tax_lots",
        "as_of",
        "created_at",
        "updated_at",
    }
    assert columns["account_id"].nullable is False
    assert columns["sync_run_id"].nullable is True
    assert columns["symbol"].nullable is False
    assert columns["instrument_name"].nullable is True
    assert columns["quantity"].nullable is False
    assert columns["average_price"].nullable is True
    assert columns["open_pnl"].nullable is True
    assert columns["currency"].nullable is False
    assert columns["tax_lots"].nullable is True
    assert columns["source"].nullable is False
    assert columns["data_freshness_status"].nullable is False
