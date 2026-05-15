import pytest
from pydantic import ValidationError

from app.schemas.broker_sync_status import (
    BrokerSyncStatusCatalog,
    get_broker_sync_status_catalog,
)
from app.schemas.broker_connection import BrokerConnectionCreate
from app.schemas.broker_sync_run import BrokerSyncRunCreate
from app.services.broker_import import statuses


pytestmark = pytest.mark.unit


def test_broker_sync_status_constants_include_expected_values() -> None:
    assert statuses.CONNECTION_STATUSES == ("connected", "disconnected", "reauth_required", "error", "unknown")
    assert statuses.SYNC_STATUSES == (
        "idle",
        "queued",
        "running",
        "succeeded",
        "failed",
        "partially_succeeded",
        "cancelled",
    )
    assert statuses.SYNC_RUN_STATUSES == (
        "queued",
        "running",
        "succeeded",
        "failed",
        "partially_succeeded",
        "cancelled",
    )
    assert statuses.DATA_FRESHNESS_STATUSES == (
        "fresh",
        "cached",
        "delayed",
        "stale",
        "unknown",
        "error",
        "reauth_required",
    )


def test_broker_sync_status_helpers_validate_known_values() -> None:
    assert statuses.is_connection_status("connected") is True
    assert statuses.is_connection_status("expired") is False
    assert statuses.is_sync_status("idle") is True
    assert statuses.is_sync_run_status("idle") is False
    assert statuses.is_data_freshness_status("delayed") is True
    assert statuses.is_terminal_sync_status("running") is False
    assert statuses.is_terminal_sync_status("failed") is True


def test_broker_sync_status_catalog_exposes_values() -> None:
    catalog = get_broker_sync_status_catalog()

    assert isinstance(catalog, BrokerSyncStatusCatalog)
    assert catalog.connection_statuses == statuses.CONNECTION_STATUSES
    assert catalog.sync_statuses == statuses.SYNC_STATUSES
    assert catalog.sync_run_statuses == statuses.SYNC_RUN_STATUSES
    assert catalog.data_freshness_statuses == statuses.DATA_FRESHNESS_STATUSES
    assert catalog.terminal_sync_statuses == statuses.TERMINAL_SYNC_STATUSES


def test_broker_schemas_use_centralized_status_values() -> None:
    connection = BrokerConnectionCreate(
        broker_name="Demo Broker",
        provider_connection_id="demo-connection",
        connection_status="reauth_required",
        sync_status="partially_succeeded",
        data_freshness_status="delayed",
    )
    run = BrokerSyncRunCreate(
        broker_connection_id="00000000-0000-0000-0000-000000000001",
        status="partially_succeeded",
    )

    assert connection.connection_status == "reauth_required"
    assert connection.sync_status == "partially_succeeded"
    assert connection.data_freshness_status == "delayed"
    assert run.status == "partially_succeeded"


def test_sync_run_status_rejects_idle_for_run_records() -> None:
    with pytest.raises(ValidationError):
        BrokerSyncRunCreate(
            broker_connection_id="00000000-0000-0000-0000-000000000001",
            status="idle",
        )
