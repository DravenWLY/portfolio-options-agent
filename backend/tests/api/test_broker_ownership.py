import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun


pytestmark = [pytest.mark.api, pytest.mark.db]


def _create_user(client: TestClient, display_name: str) -> str:
    response = client.post("/users", json={"display_name": display_name})
    assert response.status_code == 201
    return response.json()["id"]


def _create_owned_broker_resources(db_session: Session, user_id: str):
    account = Account(
        user_id=user_id,
        broker_name="Fidelity Demo",
        account_type="taxable_individual",
        display_name="Demo Account",
        is_manual=False,
    )
    db_session.add(account)
    db_session.flush()
    connection = BrokerConnection(
        user_id=user_id,
        provider="snaptrade",
        broker_name="Fidelity Demo",
        provider_connection_id="demo-connection",
    )
    db_session.add(connection)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        account_id=account.id,
        provider_account_id="demo-provider-account",
        display_name="Demo Broker Account",
    )
    db_session.add(broker_account)
    db_session.flush()
    sync_run = BrokerSyncRun(
        broker_connection_id=connection.id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="succeeded",
        summary={"warnings": [], "partial_failures": []},
    )
    db_session.add(sync_run)
    db_session.commit()
    return connection, broker_account, sync_run


def test_cross_user_broker_resource_access_returns_404(client: TestClient, db_session: Session) -> None:
    owner_id = _create_user(client, "Owner")
    other_id = _create_user(client, "Other")
    connection, broker_account, sync_run = _create_owned_broker_resources(db_session, owner_id)

    responses = [
        client.get(f"/users/{other_id}/broker-connections/{connection.id}/accounts"),
        client.post(f"/users/{other_id}/broker-accounts/{broker_account.id}/sync", json={"trigger": "manual"}),
        client.get(f"/users/{other_id}/broker-sync-runs/{sync_run.id}"),
    ]

    assert [response.status_code for response in responses] == [404, 404, 404]
