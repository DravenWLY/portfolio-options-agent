import pytest

from app.db.base import Base
from app.models.broker_sync_run import BrokerSyncRun


pytestmark = pytest.mark.unit


def test_broker_sync_run_model_is_registered_with_base_metadata() -> None:
    assert "broker_sync_runs" in Base.metadata.tables


def test_broker_sync_run_model_columns() -> None:
    columns = BrokerSyncRun.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "broker_connection_id",
        "broker_account_id",
        "trigger",
        "status",
        "started_at",
        "completed_at",
        "provider_request_id",
        "accounts_count",
        "positions_count",
        "transactions_count",
        "error",
        "summary",
        "created_at",
        "updated_at",
    }
    assert columns["broker_connection_id"].nullable is False
    assert columns["broker_account_id"].nullable is True
    assert columns["trigger"].nullable is False
    assert columns["status"].nullable is False
    assert columns["error"].nullable is True
    assert columns["summary"].nullable is True


def test_broker_sync_run_table_indexes() -> None:
    indexes = {index.name for index in BrokerSyncRun.__table__.indexes}

    assert "ix_broker_sync_runs_connection_started" in indexes
    assert "ix_broker_sync_runs_broker_account_id" in indexes
    assert "ix_broker_sync_runs_status" in indexes
