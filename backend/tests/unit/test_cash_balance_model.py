import pytest

from app.db.base import Base
from app.models.cash_balance import CashBalance


pytestmark = pytest.mark.unit


def test_cash_balance_model_is_registered_with_base_metadata() -> None:
    assert "cash_balances" in Base.metadata.tables


def test_cash_balance_model_columns() -> None:
    columns = CashBalance.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "account_id",
        "sync_run_id",
        "total_cash",
        "available_cash",
        "buying_power",
        "currency",
        "reserved_collateral_cash",
        "free_cash",
        "premium_income_cash",
        "dca_cash",
        "source",
        "source_ref",
        "data_freshness_status",
        "as_of",
        "created_at",
    }
    assert columns["account_id"].nullable is False
    assert columns["sync_run_id"].nullable is True
    assert columns["total_cash"].nullable is False
    assert columns["available_cash"].nullable is True
    assert columns["buying_power"].nullable is True
    assert columns["currency"].nullable is False
    assert columns["free_cash"].nullable is False
    assert columns["source"].nullable is False
    assert columns["source_ref"].nullable is True
    assert columns["data_freshness_status"].nullable is False
