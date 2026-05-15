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
        "symbol",
        "asset_type",
        "quantity",
        "cost_basis",
        "market_price",
        "market_value",
        "source",
        "source_ref",
        "data_freshness_status",
        "raw_provider_payload",
        "as_of",
        "created_at",
        "updated_at",
    }
    assert columns["account_id"].nullable is False
    assert columns["symbol"].nullable is False
    assert columns["quantity"].nullable is False
    assert columns["source"].nullable is False
    assert columns["data_freshness_status"].nullable is False
