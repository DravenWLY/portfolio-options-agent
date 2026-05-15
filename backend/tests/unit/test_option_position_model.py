import pytest

from app.db.base import Base
from app.models.option_position import OptionPosition


pytestmark = pytest.mark.unit


def test_option_position_model_is_registered_with_base_metadata() -> None:
    assert "option_positions" in Base.metadata.tables


def test_option_position_model_columns() -> None:
    columns = OptionPosition.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "account_id",
        "option_contract_id",
        "position_side",
        "quantity",
        "average_price",
        "market_price",
        "market_value",
        "status",
        "source",
        "source_ref",
        "data_freshness_status",
        "raw_provider_payload",
        "as_of",
        "opened_at",
        "closed_at",
        "created_at",
        "updated_at",
    }
    assert columns["account_id"].nullable is False
    assert columns["option_contract_id"].nullable is False
    assert columns["position_side"].nullable is False
    assert columns["quantity"].nullable is False
