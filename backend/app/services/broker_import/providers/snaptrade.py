from datetime import date
from typing import Any, Protocol

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
from app.services.broker_import.providers.snaptrade_models import (
    SnapTradeAccountResponse,
    SnapTradeBalanceResponse,
    SnapTradeConnectionPortalUrlResponse,
    SnapTradeConnectionResponse,
    SnapTradeOptionPositionResponse,
    SnapTradePositionResponse,
    SnapTradeRefreshResponse,
    SnapTradeTransactionResponse,
    SnapTradeUserRegistrationResponse,
)


class SnapTradeReadOnlyClient(Protocol):
    def register_user(self, user_ref: str) -> dict[str, Any]: ...

    def create_connection_portal_url(self, snaptrade_user_id: str, user_secret: str) -> dict[str, Any]: ...

    def list_connections(self, user_ref: str) -> list[dict[str, Any]]: ...

    def list_accounts(self, connection_ref: str) -> list[dict[str, Any]]: ...

    def get_balances(self, provider_account_id: str) -> dict[str, Any]: ...

    def get_positions(self, provider_account_id: str) -> list[dict[str, Any]]: ...

    def get_option_positions(self, provider_account_id: str) -> list[dict[str, Any]]: ...

    def get_transactions(self, provider_account_id: str, start: date, end: date) -> list[dict[str, Any]]: ...

    def refresh_account(self, provider_account_id: str) -> dict[str, Any]: ...


class SnapTradeAdapterNotConfiguredError(RuntimeError):
    """Raised when the SnapTrade adapter is used before configuration/integration exists."""


class SnapTradeAdapter(BrokerPortfolioProvider):
    provider_name = "snaptrade"

    def __init__(self, client: SnapTradeReadOnlyClient | None = None) -> None:
        self._client = client

    def _not_configured(self) -> SnapTradeAdapterNotConfiguredError:
        return SnapTradeAdapterNotConfiguredError(
            "SnapTradeAdapter is a read-only skeleton. Configure the mocked/real read-only integration in later tasks."
        )

    def _require_client(self) -> SnapTradeReadOnlyClient:
        if self._client is None:
            raise self._not_configured()
        return self._client

    def register_user(self, user_ref: str) -> SnapTradeUserRegistrationResponse:
        payload = self._require_client().register_user(user_ref)
        return SnapTradeUserRegistrationResponse.model_validate(payload)

    def create_connection_portal_url(
        self,
        snaptrade_user_id: str,
        user_secret: str,
    ) -> SnapTradeConnectionPortalUrlResponse:
        payload = self._require_client().create_connection_portal_url(snaptrade_user_id, user_secret)
        return SnapTradeConnectionPortalUrlResponse.model_validate(payload)

    def list_connections(self, user_ref: str) -> list[ProviderConnectionSnapshot]:
        payloads = self._require_client().list_connections(user_ref)
        return [
            SnapTradeConnectionResponse.model_validate(payload).to_provider_snapshot()
            for payload in payloads
        ]

    def list_accounts(self, connection_ref: str) -> list[ProviderAccountSnapshot]:
        payloads = self._require_client().list_accounts(connection_ref)
        return [
            SnapTradeAccountResponse.model_validate(payload).to_provider_snapshot()
            for payload in payloads
        ]

    def get_balances(self, provider_account_id: str) -> ProviderBalanceSnapshot:
        payload = self._require_client().get_balances(provider_account_id)
        return SnapTradeBalanceResponse.model_validate(payload).to_provider_snapshot()

    def get_positions(self, provider_account_id: str) -> list[ProviderPositionSnapshot]:
        payloads = self._require_client().get_positions(provider_account_id)
        return [
            SnapTradePositionResponse.model_validate(payload).to_provider_snapshot()
            for payload in payloads
        ]

    def get_option_positions(self, provider_account_id: str) -> list[ProviderOptionPositionSnapshot]:
        payloads = self._require_client().get_option_positions(provider_account_id)
        return [
            SnapTradeOptionPositionResponse.model_validate(payload).to_provider_snapshot()
            for payload in payloads
        ]

    def get_transactions(
        self,
        provider_account_id: str,
        start: date,
        end: date,
    ) -> list[ProviderTransactionSnapshot]:
        payloads = self._require_client().get_transactions(provider_account_id, start, end)
        return [
            SnapTradeTransactionResponse.model_validate(payload).to_provider_snapshot()
            for payload in payloads
        ]

    def refresh_account(self, provider_account_id: str) -> ProviderRefreshResult:
        payload = self._require_client().refresh_account(provider_account_id)
        return SnapTradeRefreshResponse.model_validate(payload).to_provider_result()
