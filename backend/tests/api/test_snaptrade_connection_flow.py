from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
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
            user_secret="11111111-1111-4111-8111-111111111111",
            raw_payload={"synthetic": True, "userSecret": "11111111-1111-4111-8111-111111111111"},
        )

    def create_connection_portal_url(
        self, snaptrade_user_id: str, user_secret: str, broker: str | None = None
    ):
        self.calls.append(f"create_connection_portal_url:{snaptrade_user_id}:{user_secret}")
        from app.services.broker_import.providers.snaptrade_models import SnapTradeConnectionPortalUrlResponse

        return SnapTradeConnectionPortalUrlResponse(
            portal_url="https://example.test/snaptrade/connect/demo",
            expires_at=datetime(2026, 5, 14, 16, 0, tzinfo=UTC),
        )

    def list_connections(self, user_ref: str):
        self.calls.append(f"list_connections:{user_ref}")
        from app.services.broker_import.providers.models import ProviderConnectionSnapshot

        now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
        return [
            ProviderConnectionSnapshot(
                provider="snaptrade",
                broker_name="Fidelity Demo",
                provider_connection_id="demo-connection",
                connection_status="connected",
                sync_status="succeeded",
                data_freshness_status="fresh",
                sync_timestamp=now,
                received_at=now,
                raw_payload={"provider_request_id": "demo-request"},
            )
        ]

    def list_accounts(self, connection_ref: str):
        self.calls.append(f"list_accounts:{connection_ref}")
        from app.services.broker_import.providers.models import ProviderAccountSnapshot

        now = datetime(2026, 5, 14, 15, 30, tzinfo=UTC)
        return [
            ProviderAccountSnapshot(
                provider="snaptrade",
                provider_connection_id=connection_ref,
                provider_account_id="demo-provider-account",
                display_name="Demo Taxable Account",
                account_type="taxable_individual",
                base_currency="USD",
                sync_status="succeeded",
                data_freshness_status="fresh",
                sync_timestamp=now,
                received_at=now,
                raw_payload={"synthetic": True},
            )
        ]


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
        response = client.post(f"/users/{user_id}/broker-sync/snaptrade/register")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    response_text = response.text.lower()
    assert payload["provider"] == "snaptrade"
    assert "snaptrade_user_id" not in payload
    assert "secret_ref" not in response_text
    assert "secret://" not in response_text
    assert "demo-snaptrade-user" not in response_text

    credential = db_session.get(ProviderCredentialsMetadata, payload["credential_metadata_id"])
    assert credential is not None
    assert credential.provider == "snaptrade"
    assert credential.credential_name == "snaptrade_user"
    assert credential.secret_ref is None
    assert credential.encrypted_secret_ref is not None
    raw_rows = db_session.execute(text("SELECT * FROM provider_credentials_metadata")).all()
    assert "11111111-1111-4111-8111-111111111111" not in str(raw_rows)
    assert "demo-snaptrade-user" not in str(raw_rows)


def test_create_snaptrade_connection_portal_url_returns_url_only(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id = _create_user(client)
    adapter = FakeSnapTradeConnectionAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        register_response = client.post(f"/users/{user_id}/broker-sync/snaptrade/register")
        assert register_response.status_code == 201

        portal_response = client.post(f"/users/{user_id}/broker-sync/snaptrade/connection-portal")
    finally:
        client.app.dependency_overrides.clear()

    assert portal_response.status_code == 200
    payload = portal_response.json()
    assert payload["portal_url"] == "https://example.test/snaptrade/connect/demo"
    assert "secret_ref" not in portal_response.text.lower()
    assert "encrypted_secret_ref" not in portal_response.text.lower()
    assert "secret://" not in portal_response.text.lower()
    assert any(call.startswith("create_connection_portal_url:") for call in adapter.calls)


def test_create_snaptrade_connection_portal_before_registration_returns_409(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id = _create_user(client)
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: FakeSnapTradeConnectionAdapter()

    try:
        response = client.post(f"/users/{user_id}/broker-sync/snaptrade/connection-portal")
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
        response = client.post(f"/users/{user_id}/broker-sync/snaptrade/register")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["detail"] == "Broker provider request failed"


def test_register_snaptrade_user_is_idempotent(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id = _create_user(client)
    adapter = FakeSnapTradeConnectionAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        first = client.post(f"/users/{user_id}/broker-sync/snaptrade/register")
        second = client.post(f"/users/{user_id}/broker-sync/snaptrade/register")
    finally:
        client.app.dependency_overrides.clear()

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["credential_metadata_id"] == second.json()["credential_metadata_id"]
    assert len(adapter.calls) == 1
    assert adapter.calls[0].startswith("register_user:poa_")


def test_refresh_snaptrade_connections_endpoint_persists_safe_records(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id = _create_user(client)
    adapter = FakeSnapTradeConnectionAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        response = client.post(f"/users/{user_id}/broker-sync/snaptrade/refresh-connections")
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert "provider_request_id" not in payload
    assert "provider_request_id" not in payload["summary"]
    assert "raw_payload" not in response.text
    assert adapter.calls == [f"list_connections:{user_id}", "list_accounts:demo-connection"]
