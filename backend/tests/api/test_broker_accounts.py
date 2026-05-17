import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection


pytestmark = [pytest.mark.api, pytest.mark.db]


def _create_connection(client: TestClient, db_session: Session) -> BrokerConnection:
    user_response = client.post("/users", json={"display_name": "Broker Account Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    connection = BrokerConnection(
        user_id=user_id,
        provider="snaptrade",
        broker_name="Fidelity Demo",
        provider_connection_id="demo-connection",
        connection_status="connected",
        sync_status="succeeded",
        data_freshness_status="fresh",
    )
    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    return connection


def test_list_broker_accounts_for_connection(
    client: TestClient,
    db_session: Session,
) -> None:
    connection = _create_connection(client, db_session)
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        provider_account_id="demo-provider-account",
        display_name="Demo Taxable Account",
        account_type="taxable_individual",
        base_currency="USD",
        sync_status="succeeded",
        data_freshness_status="fresh",
        raw_payload={"synthetic": True, "private_provider_detail": "not returned"},
    )
    db_session.add(broker_account)
    db_session.commit()

    response = client.get(f"/users/{connection.user_id}/broker-connections/{connection.id}/accounts")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert "provider_account_id" not in payload[0]
    assert payload[0]["account_type"] == "taxable_individual"
    assert "raw_payload" not in response.text
    assert "private_provider_detail" not in response.text


def test_list_broker_accounts_for_missing_connection_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.get(
        "/users/00000000-0000-0000-0000-000000000001/"
        "broker-connections/00000000-0000-0000-0000-000000000001/accounts"
    )

    assert response.status_code == 404
