from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun
from app.models.user import User


pytestmark = [pytest.mark.api, pytest.mark.db]


def _create_broker_freshness_records(db_session: Session) -> tuple[User, User, BrokerAccount, BrokerSyncRun]:
    owner = User(display_name="Broker Freshness Owner")
    other_user = User(display_name="Other Broker Freshness User")
    db_session.add_all([owner, other_user])
    db_session.flush()

    account = Account(
        user_id=owner.id,
        broker_name="Fidelity Demo",
        account_type="taxable_individual",
        display_name="Freshness Demo Account",
        is_manual=False,
    )
    db_session.add(account)
    db_session.flush()

    connection = BrokerConnection(
        user_id=owner.id,
        provider="snaptrade",
        broker_name="Fidelity Demo",
        provider_connection_id="freshness-demo-connection",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="cached",
        last_successful_sync_at=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
        last_attempted_sync_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
    )
    db_session.add(connection)
    db_session.flush()

    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        account_id=account.id,
        provider_account_id="freshness-demo-account",
        display_name="Freshness Demo Account",
        account_type="taxable_individual",
        base_currency="USD",
        sync_status="succeeded",
        data_freshness_status="cached",
        last_successful_sync_at=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
    )
    db_session.add(broker_account)
    db_session.flush()

    sync_run = BrokerSyncRun(
        broker_connection_id=connection.id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        started_at=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
        completed_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
        provider_request_id="freshness-demo-request",
        accounts_count=1,
        positions_count=2,
        summary={"warnings": [], "partial_failures": []},
    )
    db_session.add(sync_run)
    db_session.commit()
    db_session.refresh(owner)
    db_session.refresh(other_user)
    db_session.refresh(broker_account)
    db_session.refresh(sync_run)
    return owner, other_user, broker_account, sync_run


def test_broker_account_freshness_is_separate_from_market_quote_freshness(
    client: TestClient,
    db_session: Session,
) -> None:
    owner, _, broker_account, sync_run = _create_broker_freshness_records(db_session)

    response = client.get(f"/users/{owner.id}/broker-accounts/{broker_account.id}/freshness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["freshness_scope"] == "broker_portfolio"
    assert payload["broker_account_id"] == str(broker_account.id)
    assert payload["account_id"] == str(broker_account.account_id)
    assert payload["provider"] == "snaptrade"
    assert payload["broker_name"] == "Fidelity Demo"
    assert payload["connection_status"] == "connected"
    assert payload["sync_status"] == "succeeded"
    assert payload["data_freshness_status"] == "cached"
    assert payload["last_successful_sync_at"] == "2026-05-14T15:30:00Z"
    assert payload["last_attempted_sync_at"] == "2026-05-14T15:31:00Z"
    assert payload["latest_sync_run_id"] == str(sync_run.id)
    assert payload["latest_sync_run_status"] == "succeeded"
    assert payload["latest_sync_run_completed_at"] == "2026-05-14T15:31:00Z"
    assert payload["requires_reauth"] is False
    assert payload["has_error"] is False
    assert "market_quote_freshness" not in payload
    assert "quote_timestamp" not in payload


def test_broker_account_freshness_flags_reauth_and_errors(
    client: TestClient,
    db_session: Session,
) -> None:
    owner, _, broker_account, _ = _create_broker_freshness_records(db_session)
    broker_account.sync_status = "failed"
    broker_account.data_freshness_status = "reauth_required"
    db_session.add(
        BrokerSyncRun(
            broker_connection_id=broker_account.broker_connection_id,
            broker_account_id=broker_account.id,
            trigger="manual",
            status="failed",
            error={"type": "BrokerProviderReauthRequiredError", "message": "Broker provider request failed"},
        )
    )
    db_session.commit()

    response = client.get(f"/users/{owner.id}/broker-accounts/{broker_account.id}/freshness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sync_status"] == "failed"
    assert payload["data_freshness_status"] == "reauth_required"
    assert payload["requires_reauth"] is True
    assert payload["has_error"] is True
    assert payload["latest_sync_run_status"] == "failed"


def test_broker_account_freshness_uses_latest_run_status_for_error_flag(
    client: TestClient,
    db_session: Session,
) -> None:
    owner, _, broker_account, _ = _create_broker_freshness_records(db_session)
    older_failed_run = BrokerSyncRun(
        broker_connection_id=broker_account.broker_connection_id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="failed",
        error={"type": "SyntheticError", "message": "Broker provider request failed"},
        created_at=datetime(2026, 5, 14, 15, 32, tzinfo=UTC),
    )
    newer_succeeded_run = BrokerSyncRun(
        broker_connection_id=broker_account.broker_connection_id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        error=None,
        completed_at=datetime(2026, 5, 14, 15, 34, tzinfo=UTC),
        created_at=datetime(2026, 5, 14, 15, 34, tzinfo=UTC),
    )
    db_session.add_all([older_failed_run, newer_succeeded_run])
    db_session.commit()

    response = client.get(f"/users/{owner.id}/broker-accounts/{broker_account.id}/freshness")

    assert response.status_code == 200
    payload = response.json()
    assert payload["latest_sync_run_status"] == "succeeded"
    assert payload["has_error"] is False
    assert payload["requires_reauth"] is False


def test_broker_account_freshness_returns_404_for_cross_user_access(
    client: TestClient,
    db_session: Session,
) -> None:
    _, other_user, broker_account, _ = _create_broker_freshness_records(db_session)

    response = client.get(f"/users/{other_user.id}/broker-accounts/{broker_account.id}/freshness")

    assert response.status_code == 404
