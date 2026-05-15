from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes import broker_sync as broker_sync_routes
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.services.broker_import.providers.exceptions import BrokerProviderReauthRequiredError
from app.services.broker_import.providers.models import (
    ProviderBalanceSnapshot,
    ProviderOptionPositionSnapshot,
    ProviderPositionSnapshot,
    ProviderRefreshResult,
)


pytestmark = [pytest.mark.api, pytest.mark.db]


class FakeSnapTradeSyncAdapter:
    provider_name = "snaptrade"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def refresh_account(self, provider_account_id: str) -> ProviderRefreshResult:
        self.calls.append(f"refresh_account:{provider_account_id}")
        return ProviderRefreshResult(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            status="succeeded",
            started_at=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
            completed_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
            provider_request_id="demo-refresh",
            accounts_count=1,
            transactions_count=0,
        )

    def get_balances(self, provider_account_id: str) -> ProviderBalanceSnapshot:
        self.calls.append(f"get_balances:{provider_account_id}")
        return ProviderBalanceSnapshot(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            total_cash=Decimal("10000.00"),
            available_cash=Decimal("7500.00"),
            buying_power=Decimal("10000.00"),
            currency="USD",
            sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
            received_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
            sync_status="succeeded",
            data_freshness_status="fresh",
        )

    def get_positions(self, provider_account_id: str) -> list[ProviderPositionSnapshot]:
        self.calls.append(f"get_positions:{provider_account_id}")
        return [
            ProviderPositionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                symbol="VOO",
                asset_type="etf",
                quantity=Decimal("10"),
                market_value=Decimal("4500.00"),
                currency="USD",
                sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                received_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                sync_status="succeeded",
                data_freshness_status="fresh",
            )
        ]

    def get_option_positions(self, provider_account_id: str) -> list[ProviderOptionPositionSnapshot]:
        self.calls.append(f"get_option_positions:{provider_account_id}")
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
                sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                received_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                sync_status="succeeded",
                data_freshness_status="fresh",
            )
        ]


class FailingSnapTradeSyncAdapter(FakeSnapTradeSyncAdapter):
    def refresh_account(self, provider_account_id: str) -> ProviderRefreshResult:
        self.calls.append(f"refresh_account:{provider_account_id}")
        raise BrokerProviderReauthRequiredError("Broker connection requires reauthorization")


def _create_broker_account(client: TestClient, db_session: Session) -> BrokerAccount:
    user_response = client.post("/users", json={"display_name": "Sync Owner"})
    assert user_response.status_code == 201
    connection = BrokerConnection(
        user_id=user_response.json()["id"],
        provider="snaptrade",
        broker_name="Fidelity Demo",
        provider_connection_id="demo-connection",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="unknown",
    )
    db_session.add(connection)
    db_session.flush()
    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        provider_account_id="demo-provider-account",
        display_name="Demo Taxable Account",
        account_type="taxable_individual",
        base_currency="USD",
        sync_status="idle",
        data_freshness_status="unknown",
    )
    db_session.add(broker_account)
    db_session.commit()
    db_session.refresh(broker_account)
    return broker_account


def test_sync_broker_account_creates_traceable_sync_run(
    client: TestClient,
    db_session: Session,
) -> None:
    broker_account = _create_broker_account(client, db_session)
    adapter = FakeSnapTradeSyncAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        response = client.post(f"/broker-accounts/{broker_account.id}/sync", json={"trigger": "manual"})
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["broker_account_id"] == str(broker_account.id)
    assert payload["status"] == "succeeded"
    assert payload["positions_count"] == 2
    assert payload["summary"] == {
        "balance_currency": "USD",
        "stock_positions_count": 1,
        "option_positions_count": 1,
    }
    assert adapter.calls == [
        "refresh_account:demo-provider-account",
        "get_balances:demo-provider-account",
        "get_positions:demo-provider-account",
        "get_option_positions:demo-provider-account",
    ]


def test_sync_broker_account_reauth_error_returns_failed_sync_run(
    client: TestClient,
    db_session: Session,
) -> None:
    broker_account = _create_broker_account(client, db_session)
    adapter = FailingSnapTradeSyncAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        response = client.post(f"/broker-accounts/{broker_account.id}/sync", json={"trigger": "manual"})
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["error"]["type"] == "BrokerProviderReauthRequiredError"
    assert "reauthorization" in payload["error"]["message"]


def test_sync_missing_broker_account_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.post("/broker-accounts/00000000-0000-0000-0000-000000000001/sync")

    assert response.status_code == 404
