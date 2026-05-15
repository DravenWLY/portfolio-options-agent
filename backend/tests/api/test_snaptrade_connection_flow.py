from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes import broker_sync as broker_sync_routes
from app.models.provider_credentials_metadata import ProviderCredentialsMetadata
from app.services.broker_import.providers.exceptions import BrokerProviderUnavailableError


pytestmark = [pytest.mark.api, pytest.mark.db]


class FakeSnapTradeConnectionAdapter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def register_user(self, user_ref: str):
        self.calls.append(f"register_user:{user_ref}")
        from app.services.broker_import.providers.snaptrade_models import SnapTradeUserRegistrationResponse

        return SnapTradeUserRegistrationResponse(
            snaptrade_user_id=f"demo-snaptrade-user-{user_ref}",
            user_secret_ref=f"secret://snaptrade/{user_ref}",
            raw_payload={"synthetic": True},
        )

    def create_connection_portal_url(self, snaptrade_user_id: str, user_secret_ref: str):
        self.calls.append(f"create_connection_portal_url:{snaptrade_user_id}:{user_secret_ref}")
        from app.services.broker_import.providers.snaptrade_models import SnapTradeConnectionPortalUrlResponse

        return SnapTradeConnectionPortalUrlResponse(
            portal_url="https://example.test/snaptrade/connect/demo",
            expires_at=datetime(2026, 5, 14, 16, 0, tzinfo=UTC),
        )


class FailingSnapTradeConnectionAdapter:
    def register_user(self, user_ref: str):
        raise BrokerProviderUnavailableError("SnapTrade unavailable")


def _create_user(client: TestClient) -> str:
    response = client.post("/users", json={"display_name": "Broker Sync User"})
    assert response.status_code == 201
    return response.json()["id"]


def test_register_snaptrade_user_stores_metadata_without_returning_secret(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id = _create_user(client)
    adapter = FakeSnapTradeConnectionAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        response = client.post("/broker-sync/snaptrade/users", json={"user_id": user_id})
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    response_text = response.text.lower()
    assert payload["provider"] == "snaptrade"
    assert payload["snaptrade_user_id"] == f"demo-snaptrade-user-{user_id}"
    assert "secret_ref" not in response_text
    assert "secret://" not in response_text

    credential = db_session.get(ProviderCredentialsMetadata, payload["credential_metadata_id"])
    assert credential is not None
    assert credential.provider == "snaptrade"
    assert credential.credential_name == "snaptrade_user"
    assert credential.secret_ref == f"secret://snaptrade/{user_id}"


def test_create_snaptrade_connection_portal_url_returns_url_only(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id = _create_user(client)
    adapter = FakeSnapTradeConnectionAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        register_response = client.post("/broker-sync/snaptrade/users", json={"user_id": user_id})
        assert register_response.status_code == 201

        portal_response = client.post("/broker-sync/snaptrade/connection-portal", json={"user_id": user_id})
    finally:
        client.app.dependency_overrides.clear()

    assert portal_response.status_code == 200
    payload = portal_response.json()
    assert payload["portal_url"] == "https://example.test/snaptrade/connect/demo"
    assert "secret_ref" not in portal_response.text.lower()
    assert "secret://" not in portal_response.text.lower()
    assert any(call.startswith("create_connection_portal_url:") for call in adapter.calls)


def test_create_snaptrade_connection_portal_before_registration_returns_409(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id = _create_user(client)
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: FakeSnapTradeConnectionAdapter()

    try:
        response = client.post("/broker-sync/snaptrade/connection-portal", json={"user_id": user_id})
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 409


def test_register_snaptrade_user_provider_failure_returns_503(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id = _create_user(client)
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: FailingSnapTradeConnectionAdapter()

    try:
        response = client.post("/broker-sync/snaptrade/users", json={"user_id": user_id})
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 503
    assert "SnapTrade unavailable" in response.json()["detail"]
