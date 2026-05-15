from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.services.broker_import.providers.exceptions import (
    BrokerProviderAuthError,
    BrokerProviderError,
    BrokerProviderRateLimitError,
    BrokerProviderReauthRequiredError,
    BrokerProviderStaleDataError,
    BrokerProviderUnavailableError,
    map_snaptrade_error,
)
from app.services.broker_import.providers.snaptrade_models import (
    SnapTradeConnectionResponse,
    SnapTradeAccountResponse,
    SnapTradeBalanceResponse,
    SnapTradeConnectionPortalUrlResponse,
    SnapTradeOptionPositionResponse,
    SnapTradePositionResponse,
    SnapTradeRefreshResponse,
    SnapTradeTransactionResponse,
    SnapTradeUserRegistrationResponse,
)


pytestmark = [pytest.mark.adapter, pytest.mark.unit]


def test_snaptrade_error_codes_map_to_app_owned_exceptions() -> None:
    assert isinstance(map_snaptrade_error("provider_unavailable", "down"), BrokerProviderUnavailableError)
    assert isinstance(map_snaptrade_error("auth_error", "bad auth"), BrokerProviderAuthError)
    assert isinstance(map_snaptrade_error("reauth_required", "reconnect"), BrokerProviderReauthRequiredError)
    assert isinstance(map_snaptrade_error("rate_limited", "slow down"), BrokerProviderRateLimitError)
    assert isinstance(map_snaptrade_error("stale_data", "old"), BrokerProviderStaleDataError)
    assert isinstance(map_snaptrade_error("unknown", "generic"), BrokerProviderError)


def test_user_registration_uses_secret_reference_not_plaintext_secret() -> None:
    response = SnapTradeUserRegistrationResponse(
        snaptrade_user_id=" demo-user ",
        user_secret=" 11111111-1111-4111-8111-111111111111 ",
        raw_payload={"synthetic": True},
    )

    assert response.snaptrade_user_id == "demo-user"
    assert response.user_secret == "11111111-1111-4111-8111-111111111111"


def test_user_registration_requires_user_secret() -> None:
    with pytest.raises(ValidationError):
        SnapTradeUserRegistrationResponse(
            snaptrade_user_id="demo-user",
            user_secret="",
        )


def test_snaptrade_portal_and_account_models_validate_synthetic_payloads() -> None:
    now = datetime(2026, 5, 14, 15, 0, tzinfo=UTC)
    portal = SnapTradeConnectionPortalUrlResponse(portal_url="https://example.test/connect", expires_at=now)
    connection = SnapTradeConnectionResponse(
        broker_name="Demo Broker",
        provider_connection_id="demo-connection",
        connection_status="connected",
        sync_status="succeeded",
        data_freshness_status="fresh",
        received_at=now,
    )
    account = SnapTradeAccountResponse(
        provider_connection_id="demo-connection",
        provider_account_id="demo-account",
        display_name="Demo Account",
        account_type="taxable_individual",
        base_currency="usd",
        sync_status="succeeded",
        data_freshness_status="fresh",
        received_at=now,
    )

    assert portal.portal_url == "https://example.test/connect"
    assert account.base_currency == "USD"
    assert connection.to_provider_snapshot().provider_connection_id == "demo-connection"
    assert account.to_provider_snapshot().provider_account_id == "demo-account"


def test_snaptrade_portfolio_models_validate_synthetic_payloads() -> None:
    now = datetime(2026, 5, 14, 15, 0, tzinfo=UTC)
    balance = SnapTradeBalanceResponse(
        provider_account_id="demo-account",
        total_cash=Decimal("10000.00"),
        available_cash=Decimal("7500.00"),
        buying_power=Decimal("10000.00"),
        currency="usd",
        sync_timestamp=now,
        received_at=now,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )
    position = SnapTradePositionResponse(
        provider_account_id="demo-account",
        symbol="voo",
        asset_type="etf",
        quantity=Decimal("10"),
        market_value=Decimal("4500.00"),
        currency="usd",
        sync_timestamp=now,
        received_at=now,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )
    option = SnapTradeOptionPositionResponse(
        provider_account_id="demo-account",
        occ_symbol="voo260116p00400000",
        underlying_symbol="voo",
        position_side="short",
        quantity=Decimal("1"),
        market_value=Decimal("210.00"),
        currency="usd",
        sync_timestamp=now,
        received_at=now,
        sync_status="succeeded",
        data_freshness_status="fresh",
    )
    transaction = SnapTradeTransactionResponse(
        provider_account_id="demo-account",
        provider_transaction_id="demo-transaction",
        transaction_type="dividend",
        transaction_date=date(2026, 5, 14),
        symbol="voo",
        amount=Decimal("12.34"),
        currency="usd",
        sync_timestamp=now,
        received_at=now,
        data_freshness_status="fresh",
    )

    assert balance.currency == "USD"
    assert position.symbol == "VOO"
    assert option.occ_symbol == "VOO260116P00400000"
    assert transaction.symbol == "VOO"
    assert balance.to_provider_snapshot().total_cash == Decimal("10000.00")
    assert position.to_provider_snapshot().symbol == "VOO"
    assert option.to_provider_snapshot().position_side == "short"
    assert transaction.to_provider_snapshot().provider_transaction_id == "demo-transaction"


def test_snaptrade_models_reject_unknown_statuses() -> None:
    now = datetime(2026, 5, 14, 15, 0, tzinfo=UTC)

    with pytest.raises(ValidationError):
        SnapTradeAccountResponse(
            provider_connection_id="demo-connection",
            provider_account_id="demo-account",
            display_name="Demo Account",
            sync_status="surprising",
            data_freshness_status="fresh",
            received_at=now,
        )


def test_snaptrade_refresh_response_maps_to_provider_result() -> None:
    started_at = datetime(2026, 5, 14, 15, 0, tzinfo=UTC)
    completed_at = datetime(2026, 5, 14, 15, 1, tzinfo=UTC)
    response = SnapTradeRefreshResponse(
        provider_account_id="demo-account",
        status="succeeded",
        started_at=started_at,
        completed_at=completed_at,
        provider_request_id="demo-request",
        accounts_count=1,
        positions_count=3,
        transactions_count=2,
    )

    result = response.to_provider_result()

    assert result.status == "succeeded"
    assert result.provider_request_id == "demo-request"
    assert result.positions_count == 3
