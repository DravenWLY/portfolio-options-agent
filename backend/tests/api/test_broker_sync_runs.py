import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun


pytestmark = [pytest.mark.api, pytest.mark.db]


def test_get_broker_sync_run_status(client: TestClient, db_session: Session) -> None:
    user_response = client.post("/users", json={"display_name": "Sync Run Owner"})
    assert user_response.status_code == 201
    connection = BrokerConnection(
        user_id=user_response.json()["id"],
        provider="snaptrade",
        broker_name="Fidelity Demo",
        provider_connection_id="demo-connection",
    )
    db_session.add(connection)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        provider_account_id="demo-provider-account",
        display_name="Demo Account",
    )
    db_session.add(broker_account)
    db_session.flush()
    sync_run = BrokerSyncRun(
        broker_connection_id=connection.id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        provider_request_id="demo-request",
        accounts_count=1,
        positions_count=2,
        transactions_count=0,
        summary={"synthetic": True},
    )
    db_session.add(sync_run)
    db_session.commit()

    response = client.get(f"/broker-sync-runs/{sync_run.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(sync_run.id)
    assert payload["status"] == "succeeded"
    assert payload["provider_request_id"] == "demo-request"
    assert payload["summary"] == {"synthetic": True}


def test_get_missing_broker_sync_run_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.get("/broker-sync-runs/00000000-0000-0000-0000-000000000001")

    assert response.status_code == 404
