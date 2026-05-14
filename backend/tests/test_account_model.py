from app.db.base import Base
from app.models.account import Account


def test_account_model_is_registered_with_base_metadata() -> None:
    assert "accounts" in Base.metadata.tables


def test_account_model_columns() -> None:
    columns = Account.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "user_id",
        "broker_name",
        "account_type",
        "display_name",
        "base_currency",
        "is_manual",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert columns["user_id"].nullable is False
    assert columns["broker_name"].nullable is False
    assert columns["account_type"].nullable is False
