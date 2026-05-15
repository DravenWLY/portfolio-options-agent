from datetime import UTC, datetime

import pytest

from app.services.broker_import.providers.snaptrade import SnapTradeAdapter


pytestmark = [pytest.mark.adapter, pytest.mark.unit]


class FakeSnapTradeReadOnlyClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def register_user(self, user_ref: str) -> dict:
        self.calls.append(f"register_user:{user_ref}")
        return {
            "snaptrade_user_id": "demo-snaptrade-user",
            "user_secret_ref": "secret://snaptrade/demo-snaptrade-user",
            "raw_payload": {"synthetic": True},
        }

    def create_connection_portal_url(self, snaptrade_user_id: str, user_secret_ref: str) -> dict:
        self.calls.append(f"create_connection_portal_url:{snaptrade_user_id}:{user_secret_ref}")
        return {
            "portal_url": "https://example.test/snaptrade/connect/demo",
            "expires_at": datetime(2026, 5, 14, 16, 0, tzinfo=UTC),
            "raw_payload": {"synthetic": True},
        }

    def list_connections(self, user_ref: str) -> list[dict]:
        self.calls.append(f"list_connections:{user_ref}")
        return [
            {
                "broker_name": "Fidelity Demo",
                "provider_connection_id": "demo-connection",
                "connection_status": "connected",
                "sync_status": "succeeded",
                "data_freshness_status": "fresh",
                "sync_timestamp": datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                "received_at": datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                "raw_payload": {"synthetic": True},
            }
        ]

    def list_accounts(self, connection_ref: str) -> list[dict]:
        self.calls.append(f"list_accounts:{connection_ref}")
        return [
            {
                "provider_connection_id": connection_ref,
                "provider_account_id": "demo-account",
                "display_name": "Demo Taxable Account",
                "account_type": "taxable_individual",
                "base_currency": "usd",
                "sync_status": "succeeded",
                "data_freshness_status": "fresh",
                "sync_timestamp": datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                "received_at": datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                "raw_payload": {"synthetic": True},
            }
        ]


def test_snaptrade_adapter_registers_user_with_secret_reference_only() -> None:
    client = FakeSnapTradeReadOnlyClient()
    adapter = SnapTradeAdapter(client=client)

    response = adapter.register_user("demo-user")

    assert response.snaptrade_user_id == "demo-snaptrade-user"
    assert response.user_secret_ref == "secret://snaptrade/demo-snaptrade-user"
    assert not hasattr(response, "user_secret")
    assert client.calls == ["register_user:demo-user"]


def test_snaptrade_adapter_creates_connection_portal_url_without_frontend_secret() -> None:
    client = FakeSnapTradeReadOnlyClient()
    adapter = SnapTradeAdapter(client=client)

    response = adapter.create_connection_portal_url(
        "demo-snaptrade-user",
        "secret://snaptrade/demo-snaptrade-user",
    )

    assert response.portal_url == "https://example.test/snaptrade/connect/demo"
    assert "secret" not in response.portal_url
    assert client.calls == [
        "create_connection_portal_url:demo-snaptrade-user:secret://snaptrade/demo-snaptrade-user"
    ]


def test_snaptrade_adapter_lists_connections_and_accounts_from_mocked_client() -> None:
    client = FakeSnapTradeReadOnlyClient()
    adapter = SnapTradeAdapter(client=client)

    connections = adapter.list_connections("demo-user")
    accounts = adapter.list_accounts("demo-connection")

    assert connections[0].provider == "snaptrade"
    assert connections[0].provider_connection_id == "demo-connection"
    assert connections[0].connection_status == "connected"
    assert accounts[0].provider_account_id == "demo-account"
    assert accounts[0].base_currency == "USD"
    assert client.calls == ["list_connections:demo-user", "list_accounts:demo-connection"]
