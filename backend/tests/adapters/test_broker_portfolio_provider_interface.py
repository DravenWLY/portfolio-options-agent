from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.services.broker_import.providers.base import BrokerPortfolioProvider
from app.services.broker_import.providers.models import (
    ProviderAccountSnapshot,
    ProviderBalanceSnapshot,
    ProviderConnectionSnapshot,
    ProviderOptionPositionSnapshot,
    ProviderPositionSnapshot,
    ProviderRefreshResult,
    ProviderTransactionSnapshot,
)


pytestmark = [pytest.mark.adapter, pytest.mark.unit]


class FakeBrokerPortfolioProvider:
    def __init__(self) -> None:
        self.now = datetime(2026, 5, 14, 15, 0, tzinfo=UTC)

    def list_connections(self, user_ref: str) -> list[ProviderConnectionSnapshot]:
        return [
            ProviderConnectionSnapshot(
                provider="snaptrade",
                broker_name="Demo Fidelity",
                provider_connection_id="demo-connection",
                connection_status="connected",
                sync_status="succeeded",
                data_freshness_status="fresh",
                sync_timestamp=self.now,
                received_at=self.now,
            )
        ]

    def list_accounts(self, connection_ref: str) -> list[ProviderAccountSnapshot]:
        return [
            ProviderAccountSnapshot(
                provider="snaptrade",
                provider_connection_id=connection_ref,
                provider_account_id="demo-account",
                display_name="Demo Taxable Account",
                account_type="taxable_individual",
                base_currency="USD",
                sync_status="succeeded",
                data_freshness_status="fresh",
                sync_timestamp=self.now,
                received_at=self.now,
            )
        ]

    def get_balances(self, provider_account_id: str) -> ProviderBalanceSnapshot:
        return ProviderBalanceSnapshot(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            total_cash=Decimal("10000.00"),
            available_cash=Decimal("7500.00"),
            buying_power=Decimal("10000.00"),
            currency="USD",
            sync_timestamp=self.now,
            received_at=self.now,
            sync_status="succeeded",
            data_freshness_status="fresh",
        )

    def get_positions(self, provider_account_id: str) -> list[ProviderPositionSnapshot]:
        return [
            ProviderPositionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                symbol="VOO",
                asset_type="etf",
                quantity=Decimal("10"),
                market_value=Decimal("4500.00"),
                currency="USD",
                sync_timestamp=self.now,
                received_at=self.now,
                sync_status="succeeded",
                data_freshness_status="fresh",
            )
        ]

    def get_option_positions(self, provider_account_id: str) -> list[ProviderOptionPositionSnapshot]:
        return [
            ProviderOptionPositionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                occ_symbol="VOO260116P00400000",
                underlying_symbol="VOO",
                position_side="short",
                quantity=Decimal("1"),
                market_value=Decimal("210.00"),
                currency="USD",
                sync_timestamp=self.now,
                received_at=self.now,
                sync_status="succeeded",
                data_freshness_status="fresh",
            )
        ]

    def get_transactions(
        self,
        provider_account_id: str,
        start: date,
        end: date,
    ) -> list[ProviderTransactionSnapshot]:
        return [
            ProviderTransactionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                provider_transaction_id="demo-transaction",
                transaction_type="dividend",
                transaction_date=start,
                symbol="VOO",
                amount=Decimal("12.34"),
                quantity=None,
                currency="USD",
                sync_timestamp=self.now,
                received_at=self.now,
                data_freshness_status="fresh",
            )
        ]

    def refresh_account(self, provider_account_id: str) -> ProviderRefreshResult:
        return ProviderRefreshResult(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            status="succeeded",
            started_at=self.now,
            completed_at=self.now,
            provider_request_id="demo-refresh",
            accounts_count=1,
            positions_count=2,
            transactions_count=1,
        )


def test_fake_provider_satisfies_broker_portfolio_provider_protocol() -> None:
    provider = FakeBrokerPortfolioProvider()

    assert isinstance(provider, BrokerPortfolioProvider)


def test_provider_interface_returns_read_only_account_state() -> None:
    provider = FakeBrokerPortfolioProvider()

    connections = provider.list_connections("demo-user-ref")
    accounts = provider.list_accounts("demo-connection")
    balances = provider.get_balances("demo-account")
    positions = provider.get_positions("demo-account")
    option_positions = provider.get_option_positions("demo-account")
    transactions = provider.get_transactions("demo-account", date(2026, 5, 1), date(2026, 5, 14))
    refresh = provider.refresh_account("demo-account")

    assert connections[0].provider_connection_id == "demo-connection"
    assert accounts[0].provider_account_id == "demo-account"
    assert balances.total_cash == Decimal("10000.00")
    assert positions[0].symbol == "VOO"
    assert option_positions[0].position_side == "short"
    assert transactions[0].transaction_type == "dividend"
    assert refresh.status == "succeeded"


def test_provider_models_reject_invalid_status_values() -> None:
    now = datetime(2026, 5, 14, 15, 0, tzinfo=UTC)

    with pytest.raises(ValueError):
        ProviderAccountSnapshot(
            provider="snaptrade",
            provider_connection_id="demo-connection",
            provider_account_id="demo-account",
            display_name="Demo Account",
            account_type="taxable_individual",
            base_currency="USD",
            sync_status="mysterious",
            data_freshness_status="fresh",
            sync_timestamp=now,
            received_at=now,
        )

    with pytest.raises(ValueError):
        ProviderRefreshResult(
            provider="snaptrade",
            provider_account_id="demo-account",
            status="idle",
            started_at=now,
            completed_at=now,
        )


def test_provider_interface_does_not_expose_trading_or_market_quote_methods() -> None:
    disallowed_methods = {
        "place_order",
        "submit_order",
        "cancel_order",
        "execute_trade",
        "get_stock_quote",
        "get_option_chain",
        "stream_quotes",
    }

    assert disallowed_methods.isdisjoint(set(BrokerPortfolioProvider.__dict__))
