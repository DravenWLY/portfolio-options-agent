from datetime import UTC, datetime

import pytest

from app.services.broker_import.providers.exceptions import BrokerProviderError
from app.services.broker_import.providers.snaptrade import SnapTradeAdapter
from app.services.broker_import.providers.snaptrade_sdk_client import SnapTradeSDKClient


pytestmark = [pytest.mark.adapter, pytest.mark.unit]


class FakeSnapTradeReadOnlyClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def register_user(self, user_ref: str) -> dict:
        self.calls.append(f"register_user:{user_ref}")
        return {
            "snaptrade_user_id": "demo-snaptrade-user",
            "user_secret": "11111111-1111-4111-8111-111111111111",
            "raw_payload": {"synthetic": True},
        }

    def create_connection_portal_url(
        self, snaptrade_user_id: str, user_secret: str, broker: str | None = None
    ) -> dict:
        self.calls.append(f"create_connection_portal_url:{snaptrade_user_id}:{user_secret}")
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
    assert response.user_secret == "11111111-1111-4111-8111-111111111111"
    assert not hasattr(response, "user_secret_ref")
    assert client.calls == ["register_user:demo-user"]


def test_snaptrade_adapter_creates_connection_portal_url_without_frontend_secret() -> None:
    client = FakeSnapTradeReadOnlyClient()
    adapter = SnapTradeAdapter(client=client)

    response = adapter.create_connection_portal_url(
        "demo-snaptrade-user",
        "11111111-1111-4111-8111-111111111111",
    )

    assert response.portal_url == "https://example.test/snaptrade/connect/demo"
    assert "secret" not in response.portal_url
    assert client.calls == [
        "create_connection_portal_url:demo-snaptrade-user:11111111-1111-4111-8111-111111111111"
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


class _FakeSnapTradeResponse:
    def __init__(self, body):
        self.body = body


class _FakeSnapTradeAuth:
    def __init__(self) -> None:
        self.login_kwargs: dict | None = None

    def login_snap_trade_user(self, **kwargs):
        self.login_kwargs = kwargs
        return _FakeSnapTradeResponse({"redirectURI": "https://example.test/portal"})

    def register_snap_trade_user(self, body):
        raise RuntimeError("raw-provider-secret-token")


class _FakeSnapTrade:
    def __init__(self) -> None:
        self.authentication = _FakeSnapTradeAuth()


class _FakeSnapTradePositions:
    def get_user_account_positions(self, **kwargs):
        return _FakeSnapTradeResponse(
            [
                {
                    "symbol": {
                        "symbol": {
                            "symbol": "VOO",
                            "raw_symbol": "VOO",
                            "type": {"code": "cs", "description": "Common Stock"},
                        },
                    },
                    "units": 10,
                    "price": 450,
                    "currency": {"code": "USD"},
                },
                {
                    "symbol": {
                        "option_symbol": {
                            "ticker": "HOOD  260618C00085000",
                            "option_type": "CALL",
                            "strike_price": 85,
                            "expiration_date": "2026-06-18",
                            "underlying_symbol": {"symbol": "HOOD", "raw_symbol": "HOOD"},
                        },
                        "description": "HOOD 85 Call Jun 18 2026",
                    },
                    "units": -1,
                    "price": 290,
                    "currency": {"code": "USD"},
                },
            ]
        )


class _FakeSnapTradeOptions:
    def list_option_holdings(self, **kwargs):
        return _FakeSnapTradeResponse(
            [
                {
                    "symbol": {
                        "option_symbol": {
                            "ticker": "HOOD  260618C00085000",
                            "option_type": "CALL",
                            "strike_price": 85,
                            "expiration_date": "2026-06-18",
                            "underlying_symbol": {"symbol": "HOOD", "raw_symbol": "HOOD"},
                        },
                        "description": "HOOD 85 Call Jun 18 2026",
                    },
                    "units": -1,
                    "price": 290,
                    "currency": {"code": "USD"},
                }
            ]
        )


class _FakeSnapTradePortfolio:
    def __init__(self) -> None:
        self.account_information = _FakeSnapTradePositions()
        self.options = _FakeSnapTradeOptions()


def test_snaptrade_sdk_client_requests_read_only_connection_portal() -> None:
    snaptrade = _FakeSnapTrade()
    client = SnapTradeSDKClient(
        snaptrade=snaptrade,
        db=None,
        encryption_key="test_snaptrade_secret_encryption_key_32_chars",
    )

    response = client.create_connection_portal_url("demo-snaptrade-user", "demo-secret", broker="FIDELITY")

    assert response["portal_url"] == "https://example.test/portal"
    assert snaptrade.authentication.login_kwargs is not None
    assert snaptrade.authentication.login_kwargs["connection_type"] == "read"


def test_snaptrade_sdk_client_provider_errors_do_not_echo_raw_exception() -> None:
    client = SnapTradeSDKClient(
        snaptrade=_FakeSnapTrade(),
        db=None,
        encryption_key="test_snaptrade_secret_encryption_key_32_chars",
    )

    with pytest.raises(BrokerProviderError) as exc_info:
        client.register_user("demo-user")

    assert str(exc_info.value) == "SnapTrade register_user failed"
    assert "raw-provider-secret-token" not in str(exc_info.value)


def test_snaptrade_sdk_client_never_uses_account_number_as_display_name() -> None:
    client = SnapTradeSDKClient(
        snaptrade=_FakeSnapTrade(),
        db=None,
        encryption_key="test_snaptrade_secret_encryption_key_32_chars",
    )

    mapped = client._map_account(  # noqa: SLF001 - explicit safety regression for SDK mapping boundary.
        {
            "id": "provider-account-id",
            "number": "123456789",
            "raw_type": "Individual",
            "account_category": "INVESTMENT",
            "balance": {"total": {"currency": "USD"}},
            "sync_status": {"holdings": {"initial_sync_completed": True}},
        },
        "provider-connection-id",
        datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
    )

    assert mapped["display_name"] == "Taxable Individual Account"
    assert "123456789" not in mapped["display_name"]


def test_snaptrade_sdk_client_excludes_option_holdings_from_stock_positions() -> None:
    client = SnapTradeSDKClient(
        snaptrade=_FakeSnapTradePortfolio(),
        db=None,
        encryption_key="test_snaptrade_secret_encryption_key_32_chars",
    )
    client._creds_by_provider_account = lambda _account_id: ("demo-user", "demo-secret")  # noqa: SLF001

    positions = client.get_positions("demo-account")

    assert [position["symbol"] for position in positions] == ["VOO"]
    assert positions[0]["market_value"] == "4500"


def test_snaptrade_sdk_client_maps_short_call_option_holdings() -> None:
    client = SnapTradeSDKClient(
        snaptrade=_FakeSnapTradePortfolio(),
        db=None,
        encryption_key="test_snaptrade_secret_encryption_key_32_chars",
    )
    client._creds_by_provider_account = lambda _account_id: ("demo-user", "demo-secret")  # noqa: SLF001

    option_positions = client.get_option_positions("demo-account")

    assert option_positions == [
        {
            "provider": "snaptrade",
            "provider_account_id": "demo-account",
            "occ_symbol": "HOOD260618C00085000",
            "underlying_symbol": "HOOD",
            "position_side": "short",
            "quantity": "1",
            "market_value": "290",
            "currency": "USD",
            "sync_timestamp": option_positions[0]["sync_timestamp"],
            "received_at": option_positions[0]["received_at"],
            "sync_status": "succeeded",
            "data_freshness_status": "cached",
            "raw_payload": None,
        }
    ]
