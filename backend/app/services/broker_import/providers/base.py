from datetime import date
from typing import Protocol, runtime_checkable

from app.services.broker_import.providers.models import (
    ProviderAccountSnapshot,
    ProviderBalanceSnapshot,
    ProviderConnectionSnapshot,
    ProviderOptionPositionSnapshot,
    ProviderPositionSnapshot,
    ProviderRefreshResult,
    ProviderTransactionSnapshot,
)


@runtime_checkable
class BrokerPortfolioProvider(Protocol):
    def list_connections(self, user_ref: str) -> list[ProviderConnectionSnapshot]:
        """Return read-only broker connection state for a provider user reference."""

    def list_accounts(self, connection_ref: str) -> list[ProviderAccountSnapshot]:
        """Return provider brokerage accounts for a provider connection reference."""

    def get_balances(self, provider_account_id: str) -> ProviderBalanceSnapshot:
        """Return balance/cash state for a provider account."""

    def get_positions(self, provider_account_id: str) -> list[ProviderPositionSnapshot]:
        """Return stock, ETF, fund, and cash-equivalent positions for a provider account."""

    def get_option_positions(self, provider_account_id: str) -> list[ProviderOptionPositionSnapshot]:
        """Return option positions for a provider account."""

    def get_transactions(
        self,
        provider_account_id: str,
        start: date,
        end: date,
    ) -> list[ProviderTransactionSnapshot]:
        """Return account transactions where the provider supports read-only history."""

    def refresh_account(self, provider_account_id: str) -> ProviderRefreshResult:
        """Request or report a read-only provider account refresh."""
