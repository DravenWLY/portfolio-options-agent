from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes import broker_sync as broker_sync_routes
from app.models.account import Account
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.models.broker_sync_run import BrokerSyncRun
from app.models.cash_balance import CashBalance
from app.models.option_contract import OptionContract
from app.models.option_position import OptionPosition
from app.models.stock_position import StockPosition
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


def _create_broker_account(client: TestClient, db_session: Session) -> tuple[str, BrokerAccount]:
    user_response = client.post("/users", json={"display_name": "Sync Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    account = Account(
        user_id=user_id,
        broker_name="Fidelity Demo",
        account_type="taxable_individual",
        display_name="Demo Taxable Account",
        is_manual=False,
    )
    db_session.add(account)
    db_session.flush()
    connection = BrokerConnection(
        user_id=user_id,
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
        account_id=account.id,
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
    return user_id, broker_account


def test_sync_broker_account_creates_traceable_sync_run(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id, broker_account = _create_broker_account(client, db_session)
    adapter = FakeSnapTradeSyncAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        response = client.post(f"/users/{user_id}/broker-accounts/{broker_account.id}/sync", json={"trigger": "manual"})
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
        "partial_failures": [],
        "warnings": [],
    }
    assert "provider_request_id" not in payload
    assert adapter.calls == [
        "refresh_account:demo-provider-account",
        "get_balances:demo-provider-account",
        "get_positions:demo-provider-account",
        "get_option_positions:demo-provider-account",
    ]
    assert db_session.query(CashBalance).filter_by(account_id=broker_account.account_id).count() == 1
    assert db_session.query(StockPosition).filter_by(account_id=broker_account.account_id).count() == 1
    assert db_session.query(OptionContract).count() == 1
    assert db_session.query(OptionPosition).filter_by(account_id=broker_account.account_id).count() == 1


def test_sync_broker_account_reauth_error_returns_failed_sync_run(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id, broker_account = _create_broker_account(client, db_session)
    adapter = FailingSnapTradeSyncAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        response = client.post(f"/users/{user_id}/broker-accounts/{broker_account.id}/sync", json={"trigger": "manual"})
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "failed"
    assert payload["error"]["type"] == "BrokerProviderReauthRequiredError"
    assert payload["error"]["message"] == "Broker provider request failed"


def test_sync_missing_broker_account_returns_404(client: TestClient, db_session: Session) -> None:
    response = client.post(
        "/users/00000000-0000-0000-0000-000000000001/"
        "broker-accounts/00000000-0000-0000-0000-000000000001/sync"
    )

    assert response.status_code == 404


def test_sync_active_run_returns_409_with_in_flight_sync_run_id(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id, broker_account = _create_broker_account(client, db_session)
    active_run = BrokerSyncRun(
        broker_connection_id=broker_account.broker_connection_id,
        broker_account_id=broker_account.id,
        trigger="manual",
        status="running",
    )
    db_session.add(active_run)
    db_session.commit()

    response = client.post(f"/users/{user_id}/broker-accounts/{broker_account.id}/sync", json={"trigger": "manual"})

    assert response.status_code == 409
    assert response.json() == {"sync_run_id": str(active_run.id), "status": "running"}
