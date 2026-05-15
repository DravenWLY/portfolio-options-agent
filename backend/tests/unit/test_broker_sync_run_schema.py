from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.broker_sync_run import BrokerSyncRunCreate


pytestmark = pytest.mark.unit


def test_broker_sync_run_create_defaults_to_queued_manual_run() -> None:
    payload = BrokerSyncRunCreate(broker_connection_id=uuid4())

    assert payload.broker_account_id is None
    assert payload.trigger == "manual"
    assert payload.status == "queued"
    assert payload.accounts_count == 0
    assert payload.positions_count == 0
    assert payload.transactions_count == 0


def test_broker_sync_run_create_preserves_sanitized_metadata() -> None:
    payload = BrokerSyncRunCreate(
        broker_connection_id=uuid4(),
        broker_account_id=uuid4(),
        trigger="retry",
        status="partially_succeeded",
        started_at=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
        completed_at=datetime(2026, 5, 14, 15, 1, tzinfo=UTC),
        provider_request_id=" request-001 ",
        accounts_count=1,
        positions_count=12,
        transactions_count=3,
        error={"code": "partial_data", "message": "Synthetic warning"},
        summary={"freshness": "cached"},
    )

    assert payload.provider_request_id == "request-001"
    assert payload.accounts_count == 1
    assert payload.positions_count == 12
    assert payload.transactions_count == 3
    assert payload.error == {"code": "partial_data", "message": "Synthetic warning"}
    assert payload.summary == {"freshness": "cached"}


def test_broker_sync_run_create_rejects_negative_counts() -> None:
    with pytest.raises(ValidationError):
        BrokerSyncRunCreate(broker_connection_id=uuid4(), positions_count=-1)


def test_broker_sync_run_create_rejects_completed_before_started() -> None:
    with pytest.raises(ValidationError):
        BrokerSyncRunCreate(
            broker_connection_id=uuid4(),
            started_at=datetime(2026, 5, 14, 15, 1, tzinfo=UTC),
            completed_at=datetime(2026, 5, 14, 15, 0, tzinfo=UTC),
        )
