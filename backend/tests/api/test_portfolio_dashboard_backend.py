from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes import broker_sync as broker_sync_routes
from app.models.account import Account
from app.models.broker_account import BrokerAccount
from app.models.broker_connection import BrokerConnection
from app.services.broker_import.providers.models import (
    ProviderBalanceSnapshot,
    ProviderOptionPositionSnapshot,
    ProviderPositionSnapshot,
    ProviderRefreshResult,
)


pytestmark = [pytest.mark.api, pytest.mark.db]


class FakeCachedDashboardSyncAdapter:
    provider_name = "snaptrade"

    def refresh_account(self, provider_account_id: str) -> ProviderRefreshResult:
        return ProviderRefreshResult(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            status="succeeded",
            started_at=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
            completed_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
            provider_request_id="dashboard-demo-refresh",
            accounts_count=1,
        )

    def get_balances(self, provider_account_id: str) -> ProviderBalanceSnapshot:
        return ProviderBalanceSnapshot(
            provider="snaptrade",
            provider_account_id=provider_account_id,
            total_cash=Decimal("15000.00"),
            available_cash=Decimal("9000.00"),
            buying_power=Decimal("15000.00"),
            currency="USD",
            sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
            received_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
            sync_status="succeeded",
            data_freshness_status="cached",
        )

    def get_positions(self, provider_account_id: str) -> list[ProviderPositionSnapshot]:
        return [
            ProviderPositionSnapshot(
                provider="snaptrade",
                provider_account_id=provider_account_id,
                symbol="VOO",
                asset_type="etf",
                quantity=Decimal("10"),
                market_value=Decimal("5000.00"),
                currency="USD",
                sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                received_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                sync_status="succeeded",
                data_freshness_status="cached",
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
                market_value=Decimal("250.00"),
                currency="USD",
                sync_timestamp=datetime(2026, 5, 14, 15, 30, tzinfo=UTC),
                received_at=datetime(2026, 5, 14, 15, 31, tzinfo=UTC),
                sync_status="succeeded",
                data_freshness_status="cached",
            )
        ]


def _create_dashboard_broker_account(client: TestClient, db_session: Session) -> tuple[str, Account, BrokerAccount]:
    user_response = client.post("/users", json={"display_name": "Dashboard Backend Owner"})
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]

    account = Account(
        user_id=user_id,
        broker_name="Fidelity Demo",
        account_type="taxable_individual",
        display_name="Dashboard Backend Account",
        is_manual=False,
    )
    db_session.add(account)
    db_session.flush()

    connection = BrokerConnection(
        user_id=user_id,
        provider="snaptrade",
        broker_name="Fidelity Demo",
        provider_connection_id="dashboard-backend-connection",
        connection_status="connected",
        sync_status="idle",
        data_freshness_status="unknown",
    )
    db_session.add(connection)
    db_session.flush()

    broker_account = BrokerAccount(
        broker_connection_id=connection.id,
        account_id=account.id,
        provider_account_id="dashboard-backend-provider-account",
        display_name="Dashboard Backend Account",
        account_type="taxable_individual",
        base_currency="USD",
        sync_status="idle",
        data_freshness_status="unknown",
    )
    db_session.add(broker_account)
    db_session.commit()
    db_session.refresh(account)
    db_session.refresh(broker_account)
    return user_id, account, broker_account


def test_dashboard_backend_supports_synced_portfolio_without_market_data(
    client: TestClient,
    db_session: Session,
) -> None:
    user_id, account, broker_account = _create_dashboard_broker_account(client, db_session)
    adapter = FakeCachedDashboardSyncAdapter()
    client.app.dependency_overrides[broker_sync_routes.get_snaptrade_adapter] = lambda: adapter

    try:
        sync_response = client.post(f"/users/{user_id}/broker-accounts/{broker_account.id}/sync")
    finally:
        client.app.dependency_overrides.clear()

    assert sync_response.status_code == 201
    assert sync_response.json()["status"] == "succeeded"

    summary_response = client.get(f"/accounts/{account.id}/portfolio")
    freshness_response = client.get(f"/users/{user_id}/broker-accounts/{broker_account.id}/freshness")

    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["data_sources"] == ["snaptrade"]
    assert summary["data_freshness_statuses"] == ["cached"]
    assert Decimal(summary["total_cash"]) == Decimal("15000.00")
    assert Decimal(summary["stock_market_value"]) == Decimal("5000.00")
    assert Decimal(summary["option_market_value"]) == Decimal("-250.00")
    assert Decimal(summary["total_internal_value"]) == Decimal("19750.00")
    assert summary["broker_data_warnings"] == [
        {
            "code": "broker_data_cached",
            "severity": "warning",
            "message": "Broker portfolio holdings and cash are cached. "
            "Review the latest snapshot timestamp and verify in your broker before manual action.",
            "freshness_status": "cached",
            "source": "broker_portfolio",
        }
    ]
    assert "market_quote_freshness" not in summary
    assert "quote_timestamp" not in summary

    assert freshness_response.status_code == 200
    freshness = freshness_response.json()
    assert freshness["freshness_scope"] == "broker_portfolio"
    assert freshness["data_freshness_status"] == "cached"
    assert freshness["latest_sync_run_status"] == "succeeded"
    assert freshness["requires_reauth"] is False
    assert freshness["has_error"] is False
    assert "market_quote_freshness" not in freshness
    assert "quote_timestamp" not in freshness
