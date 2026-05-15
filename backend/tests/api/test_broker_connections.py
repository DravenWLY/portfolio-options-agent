import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection


pytestmark = [pytest.mark.api, pytest.mark.db]


def _create_user(client: TestClient) -> str:
    response = client.post("/users", json={"display_name": "Connection Owner"})
    assert response.status_code == 201
    return response.json()["id"]


def test_list_broker_connections_excludes_secret_references(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id = _create_user(client)
    connection = BrokerConnection(
        user_id=user_id,
        provider="snaptrade",
        broker_name="Fidelity Demo",
        provider_connection_id="demo-connection",
        connection_status="connected",
        sync_status="succeeded",
        data_freshness_status="fresh",
        secret_ref="secret://snaptrade/connection",
        scopes=["read_accounts", "read_positions"],
    )
    db_session.add(connection)
    db_session.commit()

    response = client.get(f"/users/{user_id}/broker-connections")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["connection_status"] == "connected"
    assert "provider_connection_id" not in payload[0]
    assert "secret_ref" not in response.text.lower()
    assert "secret://" not in response.text.lower()


def test_list_broker_connections_for_missing_user_returns_404(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.get("/users/00000000-0000-0000-0000-000000000001/broker-connections")

    assert response.status_code == 404
