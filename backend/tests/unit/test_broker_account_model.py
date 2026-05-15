import pytest

from app.db.base import Base
from app.models.broker_account import BrokerAccount


pytestmark = pytest.mark.unit


def test_broker_account_model_is_registered_with_base_metadata() -> None:
    assert "broker_accounts" in Base.metadata.tables


def test_broker_account_model_columns() -> None:
    columns = BrokerAccount.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "broker_connection_id",
        "account_id",
        "provider_account_id",
        "display_name",
        "account_type",
        "base_currency",
        "sync_status",
        "data_freshness_status",
        "last_successful_sync_at",
        "raw_payload",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert columns["broker_connection_id"].nullable is False
    assert columns["account_id"].nullable is True
    assert columns["provider_account_id"].nullable is False
    assert columns["display_name"].nullable is False


def test_broker_account_table_constraints_and_indexes() -> None:
    constraints = {constraint.name for constraint in BrokerAccount.__table__.constraints}
    indexes = {index.name for index in BrokerAccount.__table__.indexes}

    assert "uq_broker_accounts_connection_account" in constraints
    assert "ix_broker_accounts_broker_connection_id" in indexes
    assert "ix_broker_accounts_account_id" in indexes
    assert "ix_broker_accounts_connection_freshness" in indexes
