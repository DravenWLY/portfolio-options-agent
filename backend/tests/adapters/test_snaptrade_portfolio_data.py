from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.services.broker_import.providers.snaptrade import SnapTradeAdapter


pytestmark = [pytest.mark.adapter, pytest.mark.unit]


class FakeSnapTradePortfolioClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_balances(self, provider_account_id: str) -> dict:
        self.calls.append(f"get_balances:{provider_account_id}")
        return {
            "provider_account_id": provider_account_id,
            "total_cash": Decimal("10000.00"),
            "available_cash": Decimal("7500.00"),
            "buying_power": Decimal("10000.00"),
            "currency": "usd",
            "sync_timestamp": datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
            "received_at": datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
            "sync_status": "succeeded",
            "data_freshness_status": "fresh",
            "raw_payload": {"synthetic": True},
        }

    def get_positions(self, provider_account_id: str) -> list[dict]:
        self.calls.append(f"get_positions:{provider_account_id}")
        return [
            {
                "provider_account_id": provider_account_id,
                "symbol": "voo",
                "asset_type": "etf",
                "quantity": Decimal("10"),
                "market_value": Decimal("4500.00"),
                "currency": "usd",
                "sync_timestamp": datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                "received_at": datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                "sync_status": "succeeded",
                "data_freshness_status": "fresh",
                "raw_payload": {
                    "synthetic": True,
                    "provider_last_price_field_is_not_a_market_quote": "450.00",
                },
            }
        ]

    def get_option_positions(self, provider_account_id: str) -> list[dict]:
        self.calls.append(f"get_option_positions:{provider_account_id}")
        return [
            {
                "provider_account_id": provider_account_id,
                "occ_symbol": "voo260116p00400000",
                "underlying_symbol": "voo",
                "position_side": "short",
                "quantity": Decimal("1"),
                "market_value": Decimal("210.00"),
                "currency": "usd",
                "sync_timestamp": datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                "received_at": datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                "sync_status": "succeeded",
                "data_freshness_status": "fresh",
                "raw_payload": {"synthetic": True},
            }
        ]

    def get_transactions(self, provider_account_id: str, start: date, end: date) -> list[dict]:
        self.calls.append(f"get_transactions:{provider_account_id}:{start.isoformat()}:{end.isoformat()}")
        return [
            {
                "provider_account_id": provider_account_id,
                "provider_transaction_id": "demo-transaction",
                "transaction_type": "dividend",
                "transaction_date": date(2026, 5, 14),
                "symbol": "voo",
                "amount": Decimal("12.34"),
                "quantity": None,
                "currency": "usd",
                "sync_timestamp": datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                "received_at": datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                "data_freshness_status": "fresh",
                "raw_payload": {"synthetic": True},
            }
        ]

    def refresh_account(self, provider_account_id: str) -> dict:
        self.calls.append(f"refresh_account:{provider_account_id}")
        return {
            "provider_account_id": provider_account_id,
            "status": "succeeded",
            "started_at": datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
            "completed_at": datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
            "provider_request_id": "demo-refresh",
            "accounts_count": 1,
            "positions_count": 2,
            "transactions_count": 1,
        }


def test_snaptrade_adapter_reads_balances_from_mocked_client() -> None:
    client = FakeSnapTradePortfolioClient()
    adapter = SnapTradeAdapter(client=client)

    balance = adapter.get_balances("demo-account")

    assert balance.provider == "snaptrade"
    assert balance.total_cash == Decimal("10000.00")
    assert balance.available_cash == Decimal("7500.00")
    assert balance.currency == "USD"
    assert client.calls == ["get_balances:demo-account"]


def test_snaptrade_adapter_reads_stock_positions_without_market_quote_semantics() -> None:
    client = FakeSnapTradePortfolioClient()
    adapter = SnapTradeAdapter(client=client)

    positions = adapter.get_positions("demo-account")

    assert positions[0].symbol == "VOO"
    assert positions[0].market_value == Decimal("4500.00")
    assert positions[0].data_freshness_status == "fresh"
    assert not hasattr(positions[0], "quote_timestamp")
    assert not hasattr(positions[0], "bid")
    assert not hasattr(positions[0], "ask")


def test_snaptrade_adapter_reads_option_positions_from_mocked_client() -> None:
    client = FakeSnapTradePortfolioClient()
    adapter = SnapTradeAdapter(client=client)

    option_positions = adapter.get_option_positions("demo-account")

    assert option_positions[0].occ_symbol == "VOO260116P00400000"
    assert option_positions[0].underlying_symbol == "VOO"
    assert option_positions[0].position_side == "short"
    assert option_positions[0].market_value == Decimal("210.00")


def test_snaptrade_adapter_reads_transactions_and_refresh_status_from_mocked_client() -> None:
    client = FakeSnapTradePortfolioClient()
    adapter = SnapTradeAdapter(client=client)

    transactions = adapter.get_transactions("demo-account", date(2026, 5, 1), date(2026, 5, 14))
    refresh = adapter.refresh_account("demo-account")

    assert transactions[0].provider_transaction_id == "demo-transaction"
    assert transactions[0].symbol == "VOO"
    assert refresh.status == "succeeded"
    assert refresh.positions_count == 2
