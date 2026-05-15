import pytest

from app.db.base import Base
from app.models.option_contract import OptionContract


pytestmark = pytest.mark.unit


def test_option_contract_model_is_registered_with_base_metadata() -> None:
    assert "option_contracts" in Base.metadata.tables


def test_option_contract_model_columns() -> None:
    columns = OptionContract.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "occ_symbol",
        "underlying_symbol",
        "expiration_date",
        "strike",
        "option_type",
        "style",
        "multiplier",
        "created_at",
        "updated_at",
    }
    assert columns["occ_symbol"].nullable is False
    assert columns["underlying_symbol"].nullable is False
    assert columns["strike"].nullable is False
