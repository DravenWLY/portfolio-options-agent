import pytest

from app.db.base import Base
from app.models.broker_connection import BrokerConnection


pytestmark = pytest.mark.unit


def test_broker_connection_model_is_registered_with_base_metadata() -> None:
    assert "broker_connections" in Base.metadata.tables


def test_broker_connection_model_columns() -> None:
    columns = BrokerConnection.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "user_id",
        "provider",
        "broker_name",
        "provider_connection_id",
        "connection_status",
        "sync_status",
        "data_freshness_status",
        "last_successful_sync_at",
        "last_attempted_sync_at",
        "consent_expires_at",
        "secret_ref",
        "scopes",
        "raw_metadata",
        "created_at",
        "updated_at",
        "deleted_at",
    }
    assert columns["user_id"].nullable is False
    assert columns["provider"].nullable is False
    assert columns["broker_name"].nullable is False
    assert columns["provider_connection_id"].nullable is False
    assert columns["secret_ref"].nullable is True


def test_broker_connection_table_constraints_and_indexes() -> None:
    constraints = {constraint.name for constraint in BrokerConnection.__table__.constraints}
    indexes = {index.name for index in BrokerConnection.__table__.indexes}

    assert "uq_broker_connections_provider_connection" in constraints
    assert "ix_broker_connections_user_id" in indexes
    assert "ix_broker_connections_user_provider_status" in indexes
